from fastapi.testclient import TestClient

from app.main import app
from app.services import elexon_client

client = TestClient(app)


def test_imbalance_price_returns_data_from_elexon_client(monkeypatch) -> None:
    monkeypatch.setattr(
        elexon_client,
        "get_imbalance_price_history",
        lambda: [
            {
                "timestamp": "2026-07-27T12:00:00+00:00",
                "settlement_period": 25,
                "system_sell_price": 65.0,
                "system_buy_price": 65.0,
                "net_imbalance_volume": -12.5,
            }
        ],
    )

    response = client.get("/api/dashboard/imbalance-price")

    assert response.status_code == 200
    assert response.json() == [
        {
            "timestamp": "2026-07-27T12:00:00Z",
            "settlementPeriod": 25,
            "systemSellPrice": 65.0,
            "systemBuyPrice": 65.0,
            "netImbalanceVolume": -12.5,
        }
    ]


def test_demand_returns_data_from_elexon_client(monkeypatch) -> None:
    monkeypatch.setattr(
        elexon_client,
        "get_demand_history",
        lambda: [
            {
                "timestamp": "2026-07-27T12:00:00+00:00",
                "national_demand_mw": 27000.0,
                "transmission_system_demand_mw": 29000.0,
            }
        ],
    )

    response = client.get("/api/dashboard/demand")

    assert response.status_code == 200
    assert response.json() == [
        {
            "timestamp": "2026-07-27T12:00:00Z",
            "nationalDemandMw": 27000.0,
            "transmissionSystemDemandMw": 29000.0,
        }
    ]


def test_generation_mix_returns_data_from_elexon_client(monkeypatch) -> None:
    monkeypatch.setattr(
        elexon_client,
        "get_generation_mix_history",
        lambda: [
            {
                "timestamp": "2026-07-27T12:00:00+00:00",
                "fuel_type": "Wind Onshore",
                "quantity_mw": 1500.0,
            }
        ],
    )

    response = client.get("/api/dashboard/generation-mix")

    assert response.status_code == 200
    assert response.json() == [
        {
            "timestamp": "2026-07-27T12:00:00Z",
            "fuelType": "Wind Onshore",
            "quantityMw": 1500.0,
        }
    ]


def test_imbalance_price_returns_502_when_elexon_client_fails(monkeypatch) -> None:
    def raise_error() -> list[dict]:
        raise RuntimeError("upstream is down")

    monkeypatch.setattr(elexon_client, "get_imbalance_price_history", raise_error)

    response = client.get("/api/dashboard/imbalance-price")

    assert response.status_code == 502
