"""Live UK power grid dashboard.

Pulls recent grid data from Elexon's BMRS Insights API (see
`app.services.elexon_client`) so the dashboard tab can show real trends:
the imbalance price, national demand, and the generation mix by fuel type.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.core.schema import CamelModel
from app.services import elexon_client

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class ImbalancePricePoint(CamelModel):
    """One settlement period's system prices, the cost of the grid being out of balance."""

    timestamp: datetime
    settlement_period: int
    system_sell_price: float
    system_buy_price: float
    net_imbalance_volume: float


class DemandPoint(CamelModel):
    """One settlement period's national demand outturn."""

    timestamp: datetime
    national_demand_mw: float
    transmission_system_demand_mw: float


class GenerationMixPoint(CamelModel):
    """A single fuel type's generation output for one settlement period."""

    timestamp: datetime
    fuel_type: str
    quantity_mw: float


@router.get("/imbalance-price", response_model=list[ImbalancePricePoint])
def get_imbalance_price() -> list[dict]:
    try:
        return elexon_client.get_imbalance_price_history()
    except Exception as exc:  # noqa: BLE001 - any upstream failure maps to 502
        raise HTTPException(status_code=502, detail="Failed to fetch data from Elexon") from exc


@router.get("/demand", response_model=list[DemandPoint])
def get_demand() -> list[dict]:
    try:
        return elexon_client.get_demand_history()
    except Exception as exc:  # noqa: BLE001 - any upstream failure maps to 502
        raise HTTPException(status_code=502, detail="Failed to fetch data from Elexon") from exc


@router.get("/generation-mix", response_model=list[GenerationMixPoint])
def get_generation_mix() -> list[dict]:
    try:
        return elexon_client.get_generation_mix_history()
    except Exception as exc:  # noqa: BLE001 - any upstream failure maps to 502
        raise HTTPException(status_code=502, detail="Failed to fetch data from Elexon") from exc
