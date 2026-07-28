import datetime as dt

import numpy as np

from app.services import price_forecast as pf


def _row(date: dt.date, settlement_period: int, price: float) -> dict:
    return {
        "timestamp": dt.datetime.combine(date, dt.time.min, tzinfo=dt.UTC).isoformat(),
        "settlement_period": settlement_period,
        "price": price,
    }


def test_settlement_periods_for_date_handles_clock_change_days() -> None:
    # UK clocks go back on the last Sunday of October (a 25-hour day, 50
    # periods) and forward on the last Sunday of March (a 23-hour day, 46).
    assert len(pf._settlement_periods_for_date(dt.date(2026, 10, 25))) == 50
    assert len(pf._settlement_periods_for_date(dt.date(2026, 3, 29))) == 46
    assert len(pf._settlement_periods_for_date(dt.date(2026, 7, 1))) == 48


def test_engineer_features_computes_lags_and_rolling_means_per_period() -> None:
    start = dt.date(2024, 1, 1)
    # Period 1's price rises by 1 each day; period 2 is constant, to make the
    # arithmetic easy to hand-check and to confirm the two periods don't mix.
    rows = []
    for day in range(35):
        date = start + dt.timedelta(days=day)
        rows.append(_row(date, 1, price=100.0 + day))
        rows.append(_row(date, 2, price=50.0))

    frame = pf._prepare_training_frame(rows)
    period_1 = frame[frame["settlement_period"] == 1].sort_values("date").reset_index(drop=True)

    # Row for day 28 (0-indexed): lag_1d = day 27's price, lag_7d = day 21's.
    row = period_1[period_1["date"] == start + dt.timedelta(days=28)].iloc[0]
    assert row["lag_1d"] == 100.0 + 27
    assert row["lag_7d"] == 100.0 + 21
    # rolling_mean_7d over days 21-27 (prices 121..127): mean = 124.
    assert row["rolling_mean_7d"] == 124.0

    period_2 = frame[frame["settlement_period"] == 2]
    assert (period_2["lag_1d"] == 50.0).all()
    assert (period_2["rolling_mean_7d"] == 50.0).all()


def test_engineer_features_never_uses_a_different_period_on_the_same_date() -> None:
    # Period 1 is always 0.0, period 2 is always 1000.0 -- if a lag/rolling
    # feature ever leaked across periods on the same date, period 1's
    # features would pick up traces of 1000.0.
    start = dt.date(2024, 1, 1)
    rows = []
    for day in range(35):
        date = start + dt.timedelta(days=day)
        rows.append(_row(date, 1, price=0.0))
        rows.append(_row(date, 2, price=1000.0))

    frame = pf._prepare_training_frame(rows)
    period_1 = frame[frame["settlement_period"] == 1]
    for column in ["lag_1d", "lag_7d", "rolling_mean_7d", "rolling_mean_28d"]:
        assert (period_1[column] == 0.0).all(), f"{column} leaked another period's price"


def test_prepare_training_frame_drops_burn_in_rows_with_incomplete_history() -> None:
    start = dt.date(2024, 1, 1)
    rows = [_row(start + dt.timedelta(days=d), 1, price=100.0) for d in range(10)]

    frame = pf._prepare_training_frame(rows)

    # rolling_mean_28d needs 28 prior days; with only 10 days of data, every
    # row is dropped.
    assert frame.empty


def test_prepare_prediction_frame_uses_only_history_before_the_forecast_date() -> None:
    start = dt.date(2024, 1, 1)
    rows = [_row(start + dt.timedelta(days=d), 1, price=100.0 + d) for d in range(35)]
    forecast_date = start + dt.timedelta(days=35)

    frame = pf._prepare_prediction_frame(rows, forecast_date)

    assert list(frame["settlement_period"]) == [1]
    row = frame.iloc[0]
    assert row["lag_1d"] == 100.0 + 34  # yesterday's (last real day's) price
    assert row["lag_7d"] == 100.0 + 28
    # The forecast row itself must never appear in the historical rows used
    # to build it.
    assert forecast_date not in rows


def test_pinball_loss_matches_hand_computed_values() -> None:
    y_true = np.array([100.0, 100.0])
    y_pred = np.array([90.0, 110.0])

    # Under-prediction (90 < 100) at q=0.1: loss = 0.1 * 10 = 1.0.
    # Over-prediction (110 > 100) at q=0.1: loss = 0.9 * 10 = 9.0. Mean = 5.0.
    assert pf._pinball_loss(y_true, y_pred, 0.1) == 5.0
    # At q=0.5 the two asymmetric weights are equal (0.5 each), so it's half
    # of mean absolute error: 0.5 * 10 = 5.0.
    assert pf._pinball_loss(y_true, y_pred, 0.5) == 5.0


def test_empirical_coverage_matches_hand_computed_fraction() -> None:
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.5, 1.5, 1.5, 1.5])

    # Only the first value (1.0) is <= 1.5.
    assert pf._empirical_coverage(y_true, y_pred) == 0.25


def test_predict_quantiles_sorts_out_any_crossing() -> None:
    class _FakeModel:
        def __init__(self, value: float) -> None:
            self._value = value

        def predict(self, features):
            return np.full(len(features), self._value)

    # Deliberately mis-ordered: the "p10" model predicts higher than "p90".
    models = {0.1: _FakeModel(200.0), 0.5: _FakeModel(100.0), 0.9: _FakeModel(50.0)}
    frame = pf._prepare_training_frame(
        [_row(dt.date(2024, 1, 1) + dt.timedelta(days=d), 1, price=100.0) for d in range(35)]
    )

    sorted_predictions = pf._predict_quantiles(models, frame)

    assert (sorted_predictions[:, 0] <= sorted_predictions[:, 1]).all()
    assert (sorted_predictions[:, 1] <= sorted_predictions[:, 2]).all()


def test_full_pipeline_learns_a_synthetic_pattern(monkeypatch) -> None:
    """Integration-style test: fixed random_state, a small synthetic dataset
    with a deliberately learnable pattern. Asserts robust invariants (runs
    end-to-end, quantiles ordered, losses finite) and one coarse "did it learn
    anything" check, rather than exact values -- a full sklearn fit isn't
    practical to assert byte-for-byte."""
    monkeypatch.setattr(pf, "TRAINING_WINDOW_DAYS", 90)
    monkeypatch.setattr(pf, "HOLDOUT_DAYS", 14)
    monkeypatch.setattr(pf, "_FEATURE_BURN_IN_DAYS", 28)

    start = dt.date(2024, 1, 1)
    total_days = 90 + 14 + 28
    rows = []
    for day in range(total_days):
        date = start + dt.timedelta(days=day)
        rows.append(_row(date, 1, price=50.0))  # cheap period, always ~50
        rows.append(_row(date, 2, price=200.0))  # expensive period, always ~200

    frame = pf._prepare_training_frame(rows)
    holdout_cutoff = (start + dt.timedelta(days=total_days - 14 - 1)) - dt.timedelta(days=14)
    train_frame = frame[frame["date"] < holdout_cutoff]
    holdout_frame = frame[frame["date"] >= holdout_cutoff]

    models = pf._fit_quantile_models(train_frame)
    backtest = pf._evaluate_backtest(holdout_frame, models)

    for metric in backtest["quantile_metrics"]:
        assert np.isfinite(metric["pinball_loss"])
        assert metric["pinball_loss"] >= 0

    forecast_date = start + dt.timedelta(days=total_days)
    prediction_frame = pf._prepare_prediction_frame(rows, forecast_date)
    sorted_predictions = pf._predict_quantiles(models, prediction_frame)
    assert (sorted_predictions[:, 0] <= sorted_predictions[:, 1]).all()
    assert (sorted_predictions[:, 1] <= sorted_predictions[:, 2]).all()

    periods = prediction_frame["settlement_period"].to_numpy()
    cheap_period_p50 = sorted_predictions[periods == 1, 1][0]
    expensive_period_p50 = sorted_predictions[periods == 2, 1][0]
    assert expensive_period_p50 > cheap_period_p50
