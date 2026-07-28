"""Quantile regression forecast of the GB day-ahead price.

Predicts the 10th/50th/90th percentile of tomorrow's price for each
settlement period, using `elexon_client.get_day_ahead_price_training_history`
as the sole data source. Two design constraints shape everything here:

- **No leakage.** The day-ahead auction clears every settlement period of a
  day in one batch the afternoon before, so a same-day *different-period*
  value is never actually known at forecast time — only a different day's
  *same-period* value is fair game. Every lag/rolling feature is therefore
  computed via `groupby("settlement_period")`, which enforces that by
  construction. This also sidesteps the UK's 46/50-period clock-change days
  cleanly: lag features simply match by settlement period number, not
  wall-clock time, at the cost of periods 49/50 (which only exist one day a
  year) having very little history — a real, documented limitation rather
  than a special case.
- **No demand/wind features.** The dashboard only has *outturn* demand and
  generation data, not forecasts of either, so using them here would leak
  the future. Calendar features (settlement period, day of week, month) and
  the price's own history are all that's used for this first version.

The model is `sklearn.ensemble.GradientBoostingRegressor(loss="quantile")`,
fit independently once per quantile in `FORECAST_QUANTILES` (scikit-learn has
no native multi-quantile regressor). Independently-fit quantile models can
"cross" (e.g. predict a higher price for the 10th percentile than the 50th);
`_predict_quantiles` sorts each row's predictions to rule that out.

There's no database or scheduler anywhere in this backend, so training
follows the same request-driven style as the rest of it: `_get_or_train`
retrains once per calendar day, on whichever request happens to be first
that day, cached in a module-level `_state` behind a `threading.Lock` (the
forecast target only changes daily, so a wall-clock TTL isn't needed — "is
this still today's model?" is the only check).

Model quality is reported via a single chronological train/holdout split
(the last `HOLDOUT_DAYS`), not a full walk-forward retrain-every-day
backtest — a deliberate simplification for a first version, surfaced to the
user as pinball loss and quantile calibration (empirical vs. nominal
coverage) rather than hidden.
"""

from __future__ import annotations

import datetime as dt
import threading
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from app.services import elexon_client

_LONDON_TZ = ZoneInfo("Europe/London")

# Sorted ascending: `_predict_quantiles` relies on this order to label its
# sorted columns p10/p50/p90 correctly.
FORECAST_QUANTILES: tuple[float, ...] = (0.1, 0.5, 0.9)

FEATURE_COLUMNS = [
    "settlement_period",
    "day_of_week",
    "is_weekend",
    "month",
    "lag_1d",
    "lag_7d",
    "rolling_mean_7d",
    "rolling_mean_28d",
]

FEATURE_DESCRIPTIONS = {
    "settlement_period": "Which half-hour of the day (1-48, or 46/50 on UK clock-change days).",
    "day_of_week": "Monday = 0 .. Sunday = 6.",
    "is_weekend": "Saturday or Sunday.",
    "month": "Calendar month (1-12), a rough proxy for season.",
    "lag_1d": "This settlement period's price yesterday.",
    "lag_7d": "This settlement period's price a week ago — also the persistence baseline's guess.",
    "rolling_mean_7d": "Trailing 7-day mean price for this settlement period.",
    "rolling_mean_28d": "Trailing 28-day mean price for this settlement period.",
}

TRAINING_WINDOW_DAYS = 730
HOLDOUT_DAYS = 60
# Matches the longest rolling window (28d); rows before this many days into
# the fetched range can't have a full rolling_mean_28d and are dropped.
_FEATURE_BURN_IN_DAYS = 28

_MODEL_HYPERPARAMETERS: dict[str, float | int] = {
    "n_estimators": 100,
    "max_depth": 3,
    "learning_rate": 0.1,
    "random_state": 42,
}


def _settlement_periods_for_date(d: dt.date) -> list[int]:
    """The settlement periods (1-48, or 46/50 on UK clock-change days) making up
    a UK settlement day, derived from how many 30-minute periods actually
    elapse between one local midnight and the next."""
    start = dt.datetime.combine(d, dt.time.min, tzinfo=_LONDON_TZ)
    end = dt.datetime.combine(d + dt.timedelta(days=1), dt.time.min, tzinfo=_LONDON_TZ)
    period_count = int((end.astimezone(dt.UTC) - start.astimezone(dt.UTC)).total_seconds() // 1800)
    return list(range(1, period_count + 1))


def _to_labeled_rows(raw_rows: list[dict]) -> list[dict]:
    """Maps elexon_client's {timestamp, settlement_period, price} rows to
    {date, settlement_period, price}, using the UTC calendar date of each
    row's start time as the day label."""
    return [
        {
            "date": pd.Timestamp(row["timestamp"]).date(),
            "settlement_period": row["settlement_period"],
            "price": row["price"],
        }
        for row in raw_rows
    ]


def _engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Adds calendar and price-history features to a (date, settlement_period,
    price) frame. See the module docstring for why every lag/rolling feature
    is computed within a `groupby("settlement_period")` — it's what makes this
    leakage-safe. A row with `price = NaN` (used to build a prediction-time
    feature row for a not-yet-happened date) never contributes to another
    row's lag/rolling values, since shift/rolling only look backward.
    """
    frame = frame.sort_values(["settlement_period", "date"]).reset_index(drop=True)
    date_index = pd.to_datetime(frame["date"])
    frame["day_of_week"] = date_index.dt.dayofweek
    frame["is_weekend"] = frame["day_of_week"] >= 5
    frame["month"] = date_index.dt.month

    by_period = frame.groupby("settlement_period")["price"]
    frame["lag_1d"] = by_period.shift(1)
    frame["lag_7d"] = by_period.shift(7)
    # Shifted by 1 before rolling so the window covers strictly earlier days,
    # never the row's own (same-day) price.
    frame["rolling_mean_7d"] = by_period.transform(
        lambda s: s.shift(1).rolling(7, min_periods=7).mean()
    )
    frame["rolling_mean_28d"] = by_period.transform(
        lambda s: s.shift(1).rolling(28, min_periods=28).mean()
    )
    return frame


def _prepare_training_frame(raw_rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame.from_records(_to_labeled_rows(raw_rows))
    frame = _engineer_features(frame)
    return frame.dropna(subset=[*FEATURE_COLUMNS, "price"]).reset_index(drop=True)


def _prepare_prediction_frame(raw_rows: list[dict], forecast_date: dt.date) -> pd.DataFrame:
    """Builds feature rows for `forecast_date` by appending one NaN-price
    placeholder row per expected settlement period to the historical rows,
    then running them through the identical feature pipeline training uses —
    so the forecast day's lag/rolling features come purely from real prices
    before it, never from `forecast_date` itself."""
    placeholder_rows = [
        {"date": forecast_date, "settlement_period": p, "price": float("nan")}
        for p in _settlement_periods_for_date(forecast_date)
    ]
    frame = pd.DataFrame.from_records(_to_labeled_rows(raw_rows) + placeholder_rows)
    frame = _engineer_features(frame)
    forecast_rows = frame[frame["date"] == forecast_date]
    return forecast_rows.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)


def _fit_quantile_models(train_frame: pd.DataFrame) -> dict[float, GradientBoostingRegressor]:
    features = train_frame[FEATURE_COLUMNS]
    target = train_frame["price"]
    return {
        quantile: GradientBoostingRegressor(
            loss="quantile", alpha=quantile, **_MODEL_HYPERPARAMETERS
        ).fit(features, target)
        for quantile in FORECAST_QUANTILES
    }


def _predict_quantiles(
    models: dict[float, GradientBoostingRegressor], frame: pd.DataFrame
) -> np.ndarray:
    """Predicts every quantile for `frame`'s rows and sorts them per row so
    p10 <= p50 <= p90 always holds (see module docstring on quantile crossing).
    Returns an (n_rows, len(FORECAST_QUANTILES)) array, columns ascending."""
    features = frame[FEATURE_COLUMNS]
    predictions = np.column_stack([models[q].predict(features) for q in FORECAST_QUANTILES])
    return np.sort(predictions, axis=1)


def _pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, quantile: float) -> float:
    diff = y_true - y_pred
    return float(np.mean(np.maximum(quantile * diff, (quantile - 1) * diff)))


def _empirical_coverage(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Fraction of actual prices at or below the predicted quantile — a
    well-calibrated q-quantile forecast should see this land near q."""
    return float(np.mean(y_true <= y_pred))


def _evaluate_backtest(
    holdout_frame: pd.DataFrame, models: dict[float, GradientBoostingRegressor]
) -> dict:
    y_true = holdout_frame["price"].to_numpy()
    sorted_predictions = _predict_quantiles(models, holdout_frame)

    quantile_metrics = [
        {
            "quantile": quantile,
            "pinball_loss": _pinball_loss(y_true, sorted_predictions[:, i], quantile),
            "nominal_coverage": quantile,
            "empirical_coverage": _empirical_coverage(y_true, sorted_predictions[:, i]),
        }
        for i, quantile in enumerate(FORECAST_QUANTILES)
    ]

    # The persistence baseline's "prediction" is just last week's price at the
    # same settlement period — exactly the lag_7d feature.
    persistence_prediction = holdout_frame["lag_7d"].to_numpy()
    model_p50_prediction = sorted_predictions[:, FORECAST_QUANTILES.index(0.5)]
    return {
        "quantile_metrics": quantile_metrics,
        "persistence_baseline_pinball_loss_p50": _pinball_loss(y_true, persistence_prediction, 0.5),
        "model_pinball_loss_p50": _pinball_loss(y_true, model_p50_prediction, 0.5),
    }


@dataclass
class TrainedState:
    trained_on: dt.date
    trained_at: dt.datetime
    models: dict[float, GradientBoostingRegressor]
    training_window: tuple[dt.date, dt.date]
    training_row_count: int
    holdout_window: tuple[dt.date, dt.date]
    holdout_row_count: int
    backtest: dict


_state: TrainedState | None = None
_lock = threading.Lock()


def _train() -> TrainedState:
    today = dt.date.today()
    fetch_start = today - dt.timedelta(
        days=TRAINING_WINDOW_DAYS + HOLDOUT_DAYS + _FEATURE_BURN_IN_DAYS
    )
    raw_rows = elexon_client.get_day_ahead_price_training_history(fetch_start, today)
    frame = _prepare_training_frame(raw_rows)

    holdout_cutoff = today - dt.timedelta(days=HOLDOUT_DAYS)
    train_frame = frame[frame["date"] < holdout_cutoff]
    holdout_frame = frame[frame["date"] >= holdout_cutoff]

    models = _fit_quantile_models(train_frame)
    backtest = _evaluate_backtest(holdout_frame, models)

    return TrainedState(
        trained_on=today,
        trained_at=dt.datetime.now(dt.UTC),
        models=models,
        training_window=(train_frame["date"].min(), train_frame["date"].max()),
        training_row_count=len(train_frame),
        holdout_window=(holdout_frame["date"].min(), holdout_frame["date"].max()),
        holdout_row_count=len(holdout_frame),
        backtest=backtest,
    )


def _get_or_train() -> TrainedState:
    global _state
    with _lock:
        if _state is None or _state.trained_on != dt.date.today():
            _state = _train()
        return _state


def get_forecast() -> dict:
    """Tomorrow's predicted day-ahead price, as a p10/p50/p90 band per
    settlement period. A period is omitted if it doesn't yet have enough price
    history to build its features (e.g. periods 49/50 on a clock-change day)."""
    state = _get_or_train()
    forecast_date = dt.date.today() + dt.timedelta(days=1)

    fetch_start = forecast_date - dt.timedelta(days=_FEATURE_BURN_IN_DAYS + 7)
    raw_rows = elexon_client.get_day_ahead_price_training_history(
        fetch_start, forecast_date - dt.timedelta(days=1)
    )
    prediction_frame = _prepare_prediction_frame(raw_rows, forecast_date)

    points = []
    if not prediction_frame.empty:
        sorted_predictions = _predict_quantiles(state.models, prediction_frame)
        points = [
            {
                "settlement_period": int(period),
                "p10": float(sorted_predictions[i, 0]),
                "p50": float(sorted_predictions[i, 1]),
                "p90": float(sorted_predictions[i, 2]),
            }
            for i, period in enumerate(prediction_frame["settlement_period"])
        ]

    return {
        "forecast_date": forecast_date,
        "generated_at": state.trained_at,
        "quantiles": list(FORECAST_QUANTILES),
        "points": points,
    }


def get_model_info() -> dict:
    """Describes how the currently-cached model was built — the data behind
    the "how is this model built?" explainer on the forecasting page."""
    state = _get_or_train()
    return {
        "algorithm": "Gradient-boosted quantile regression "
        "(scikit-learn GradientBoostingRegressor, one model per quantile)",
        "quantiles": list(FORECAST_QUANTILES),
        "features": [
            {"name": name, "description": description}
            for name, description in FEATURE_DESCRIPTIONS.items()
        ],
        "training_window_start": state.training_window[0],
        "training_window_end": state.training_window[1],
        "training_row_count": state.training_row_count,
        "trained_at": state.trained_at,
        "hyperparameters": _MODEL_HYPERPARAMETERS,
    }


def get_backtest() -> dict:
    """Out-of-sample model quality on the holdout window: pinball loss and
    quantile calibration per quantile, plus a head-to-head pinball loss at the
    median against the naive persistence baseline (last week's price)."""
    state = _get_or_train()
    return {
        "holdout_start": state.holdout_window[0],
        "holdout_end": state.holdout_window[1],
        "holdout_row_count": state.holdout_row_count,
        "quantile_metrics": state.backtest["quantile_metrics"],
        "persistence_baseline_pinball_loss_p50": state.backtest[
            "persistence_baseline_pinball_loss_p50"
        ],
        "model_pinball_loss_p50": state.backtest["model_pinball_loss_p50"],
    }
