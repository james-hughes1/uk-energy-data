"""Client for pulling live/recent GB grid data from Elexon's BMRS Insights API.

The Insights API (https://bmrs.elexon.co.uk/) is public and needs no API key,
so this module just wraps the handful of `elexonpy` calls the dashboard needs
and reshapes the responses into plain list-of-dict records that map directly
onto the frontend's chart types.

Settlement periods are 30 minutes long and a GB "settlement day" runs on the
local (Europe/London) calendar day, so every fetch below pulls today's
settlement date plus a few previous days and keeps only the most recent
points. Pulling more than just "today" avoids a near-empty chart in the early
hours of the day, before today's settlement periods have been published.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
from elexonpy.api.demand_api import DemandApi
from elexonpy.api.generation_api import GenerationApi
from elexonpy.api.indicative_imbalance_settlement_api import (
    IndicativeImbalanceSettlementApi,
)
from elexonpy.api_client import ApiClient

_api_client = ApiClient()
_system_price_api = IndicativeImbalanceSettlementApi(_api_client)
_demand_api = DemandApi(_api_client)
_generation_api = GenerationApi(_api_client)

# Half-hourly settlement periods, ~48/day; keep the most recent day's worth.
_MAX_POINTS = 48


def _recent_settlement_dates(days_back: int = 1) -> list[dt.date]:
    """Today's settlement date plus `days_back` previous days, oldest first."""
    today = dt.date.today()
    return [today - dt.timedelta(days=i) for i in range(days_back, -1, -1)]


def get_imbalance_price_history() -> list[dict]:
    """Recent settlement system buy/sell prices (the GB imbalance price)."""
    records = []
    for settlement_date in _recent_settlement_dates():
        # `format="json"` works around an elexonpy bug: with no query params
        # at all, its internal `call_api` references an unset local variable.
        response = _system_price_api.balancing_settlement_system_prices_settlement_date_get(
            settlement_date.isoformat(), format="json"
        )
        records.extend(row.to_dict() for row in response.data)

    if not records:
        return []

    frame = pd.DataFrame.from_records(records).sort_values("start_time").tail(_MAX_POINTS)
    return [
        {
            "timestamp": pd.Timestamp(row.start_time).isoformat(),
            "settlement_period": int(row.settlement_period),
            "system_sell_price": row.system_sell_price,
            "system_buy_price": row.system_buy_price,
            "net_imbalance_volume": row.net_imbalance_volume,
        }
        for row in frame.itertuples()
    ]


def get_demand_history() -> list[dict]:
    """Recent national demand outturn (INDO/ITSDO)."""
    records = []
    for settlement_date in _recent_settlement_dates():
        response = _demand_api.demand_outturn_get(
            settlement_date_from=settlement_date.isoformat(),
            settlement_date_to=settlement_date.isoformat(),
        )
        records.extend(row.to_dict() for row in response.data)

    if not records:
        return []

    frame = pd.DataFrame.from_records(records).sort_values("start_time").tail(_MAX_POINTS)
    return [
        {
            "timestamp": pd.Timestamp(row.start_time).isoformat(),
            "national_demand_mw": row.initial_demand_outturn,
            "transmission_system_demand_mw": row.initial_transmission_system_demand_outturn,
        }
        for row in frame.itertuples()
    ]


def get_generation_mix_history(hours_back: int = 24) -> list[dict]:
    """Recent actual generation output, broken down by fuel type (PSR type)."""
    now = dt.datetime.now(dt.UTC)
    response = _generation_api.generation_actual_per_type_get(
        _from=(now - dt.timedelta(hours=hours_back)).isoformat(),
        to=now.isoformat(),
    )

    return [
        {
            "timestamp": pd.Timestamp(period.start_time).isoformat(),
            "fuel_type": value.psr_type,
            "quantity_mw": value.quantity,
        }
        for period in response.data
        for value in period.data
    ]
