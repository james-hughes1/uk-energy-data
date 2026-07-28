"""GB day-ahead price forecasting.

Serves a quantile regression forecast of tomorrow's day-ahead price (see
`app.services.price_forecast` for the model itself), alongside the
information needed to explain how that model is built and how good it
actually is: its feature set and training window, and an out-of-sample
backtest against a naive persistence baseline.

Unlike the dashboard endpoints, these take no `start`/`end` query params —
the training and holdout windows are fixed internal constants for this first
version, not something callers choose per request.
"""

import datetime as dt

from fastapi import APIRouter, HTTPException

from app.core.schema import CamelModel
from app.services import price_forecast

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])


class QuantilePricePoint(CamelModel):
    """One settlement period's predicted price band."""

    settlement_period: int
    p10: float
    p50: float
    p90: float


class DayAheadForecastResponse(CamelModel):
    """Tomorrow's predicted day-ahead price, as a quantile band per settlement
    period. `points` may have fewer than the expected number of periods if
    some don't yet have enough price history to build their features."""

    forecast_date: dt.date
    generated_at: dt.datetime
    quantiles: list[float]
    points: list[QuantilePricePoint]


class ModelFeatureDescription(CamelModel):
    name: str
    description: str


class ModelInfoResponse(CamelModel):
    """Describes how the currently-cached model was built."""

    algorithm: str
    quantiles: list[float]
    features: list[ModelFeatureDescription]
    training_window_start: dt.date
    training_window_end: dt.date
    training_row_count: int
    trained_at: dt.datetime
    hyperparameters: dict[str, float | int]


class QuantileBacktestMetric(CamelModel):
    quantile: float
    pinball_loss: float
    nominal_coverage: float
    empirical_coverage: float


class BacktestResponse(CamelModel):
    """Out-of-sample model quality on a holdout window, per quantile, plus a
    head-to-head comparison against the naive persistence baseline at the
    median."""

    holdout_start: dt.date
    holdout_end: dt.date
    holdout_row_count: int
    quantile_metrics: list[QuantileBacktestMetric]
    persistence_baseline_pinball_loss_p50: float
    model_pinball_loss_p50: float


@router.get("/day-ahead-forecast", response_model=DayAheadForecastResponse)
def get_day_ahead_forecast() -> dict:
    try:
        return price_forecast.get_forecast()
    except Exception as exc:  # noqa: BLE001 - any upstream failure maps to 502
        raise HTTPException(status_code=502, detail="Failed to fetch data from Elexon") from exc


@router.get("/model-info", response_model=ModelInfoResponse)
def get_model_info() -> dict:
    try:
        return price_forecast.get_model_info()
    except Exception as exc:  # noqa: BLE001 - any upstream failure maps to 502
        raise HTTPException(status_code=502, detail="Failed to fetch data from Elexon") from exc


@router.get("/backtest", response_model=BacktestResponse)
def get_backtest() -> dict:
    try:
        return price_forecast.get_backtest()
    except Exception as exc:  # noqa: BLE001 - any upstream failure maps to 502
        raise HTTPException(status_code=502, detail="Failed to fetch data from Elexon") from exc
