"""Live UK power grid dashboard.

Pulls grid data over a caller-supplied date range from Elexon's BMRS
Insights API (see `app.services.elexon_client`) so the dashboard tab can
show trends in the imbalance price, national demand, and the generation
mix by fuel type — from the last 24 hours back to `EARLIEST_AVAILABLE_DATE`.
"""

import datetime as dt

from fastapi import APIRouter, HTTPException

from app.core.schema import CamelModel
from app.services import elexon_client

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class ImbalancePricePoint(CamelModel):
    """One settlement period's system prices, the cost of the grid being out of balance."""

    timestamp: dt.datetime
    settlement_period: int
    system_sell_price: float
    system_buy_price: float
    net_imbalance_volume: float


class DemandPoint(CamelModel):
    """One settlement period's national demand outturn."""

    timestamp: dt.datetime
    national_demand_mw: float
    transmission_system_demand_mw: float


class GenerationMixPoint(CamelModel):
    """A single fuel type's generation output for one settlement period."""

    timestamp: dt.datetime
    fuel_type: str
    quantity_mw: float


def _resolve_range(start: dt.date | None, end: dt.date | None) -> tuple[dt.date, dt.date]:
    """Fills in defaults (last 24h) and clamps to [EARLIEST_AVAILABLE_DATE, today]."""
    today = dt.date.today()
    resolved_end = min(end, today) if end is not None else today
    resolved_start = start if start is not None else resolved_end - dt.timedelta(days=1)
    resolved_start = max(resolved_start, elexon_client.EARLIEST_AVAILABLE_DATE)

    if resolved_start > resolved_end:
        raise HTTPException(status_code=400, detail="start must not be after end")

    return resolved_start, resolved_end


@router.get("/imbalance-price", response_model=list[ImbalancePricePoint])
def get_imbalance_price(
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> list[dict]:
    resolved_start, resolved_end = _resolve_range(start, end)
    try:
        return elexon_client.get_imbalance_price_history(resolved_start, resolved_end)
    except Exception as exc:  # noqa: BLE001 - any upstream failure maps to 502
        raise HTTPException(status_code=502, detail="Failed to fetch data from Elexon") from exc


@router.get("/demand", response_model=list[DemandPoint])
def get_demand(
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> list[dict]:
    resolved_start, resolved_end = _resolve_range(start, end)
    try:
        return elexon_client.get_demand_history(resolved_start, resolved_end)
    except Exception as exc:  # noqa: BLE001 - any upstream failure maps to 502
        raise HTTPException(status_code=502, detail="Failed to fetch data from Elexon") from exc


@router.get("/generation-mix", response_model=list[GenerationMixPoint])
def get_generation_mix(
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> list[dict]:
    resolved_start, resolved_end = _resolve_range(start, end)
    try:
        return elexon_client.get_generation_mix_history(resolved_start, resolved_end)
    except Exception as exc:  # noqa: BLE001 - any upstream failure maps to 502
        raise HTTPException(status_code=502, detail="Failed to fetch data from Elexon") from exc
