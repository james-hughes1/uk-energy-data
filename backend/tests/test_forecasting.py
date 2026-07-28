import datetime as dt

from fastapi.testclient import TestClient

from app.main import app
from app.services import price_forecast

client = TestClient(app)


def test_day_ahead_forecast_returns_data_from_price_forecast(monkeypatch) -> None:
    monkeypatch.setattr(
        price_forecast,
        "get_forecast",
        lambda: {
            "forecast_date": dt.date(2026, 7, 29),
            "generated_at": dt.datetime(2026, 7, 28, 12, 0, tzinfo=dt.UTC),
            "quantiles": [0.1, 0.5, 0.9],
            "points": [{"settlement_period": 1, "p10": 80.0, "p50": 100.0, "p90": 130.0}],
        },
    )

    response = client.get("/api/forecasting/day-ahead-forecast")

    assert response.status_code == 200
    assert response.json() == {
        "forecastDate": "2026-07-29",
        "generatedAt": "2026-07-28T12:00:00Z",
        "quantiles": [0.1, 0.5, 0.9],
        "points": [{"settlementPeriod": 1, "p10": 80.0, "p50": 100.0, "p90": 130.0}],
    }


def test_model_info_returns_data_from_price_forecast(monkeypatch) -> None:
    monkeypatch.setattr(
        price_forecast,
        "get_model_info",
        lambda: {
            "algorithm": "Gradient-boosted quantile regression",
            "quantiles": [0.1, 0.5, 0.9],
            "features": [{"name": "lag_7d", "description": "Last week's price."}],
            "training_window_start": dt.date(2024, 7, 29),
            "training_window_end": dt.date(2026, 5, 28),
            "training_row_count": 35000,
            "trained_at": dt.datetime(2026, 7, 28, 12, 0, tzinfo=dt.UTC),
            "hyperparameters": {"n_estimators": 100, "max_depth": 3},
        },
    )

    response = client.get("/api/forecasting/model-info")

    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "Gradient-boosted quantile regression"
    assert body["trainingRowCount"] == 35000
    assert body["features"] == [{"name": "lag_7d", "description": "Last week's price."}]


def test_backtest_returns_data_from_price_forecast(monkeypatch) -> None:
    monkeypatch.setattr(
        price_forecast,
        "get_backtest",
        lambda: {
            "holdout_start": dt.date(2026, 5, 29),
            "holdout_end": dt.date(2026, 7, 28),
            "holdout_row_count": 2914,
            "quantile_metrics": [
                {
                    "quantile": 0.5,
                    "pinball_loss": 11.6,
                    "nominal_coverage": 0.5,
                    "empirical_coverage": 0.34,
                }
            ],
            "persistence_baseline_pinball_loss_p50": 14.7,
            "model_pinball_loss_p50": 11.6,
        },
    )

    response = client.get("/api/forecasting/backtest")

    assert response.status_code == 200
    body = response.json()
    assert body["holdoutRowCount"] == 2914
    assert body["quantileMetrics"][0]["empiricalCoverage"] == 0.34
    assert body["modelPinballLossP50"] < body["persistenceBaselinePinballLossP50"]


def test_day_ahead_forecast_returns_502_when_price_forecast_fails(monkeypatch) -> None:
    def raise_error() -> dict:
        raise RuntimeError("upstream is down")

    monkeypatch.setattr(price_forecast, "get_forecast", raise_error)

    response = client.get("/api/forecasting/day-ahead-forecast")

    assert response.status_code == 502
