"""Client for pulling UK grid data from Elexon's BMRS Insights API, over an
arbitrary date range.

The Insights API (https://bmrs.elexon.co.uk/) is public and needs no API key,
so this module just calls it directly with `requests` and reshapes the JSON
into plain list-of-dict records that map onto the frontend's chart types.
`elexonpy` (the community client) was tried first, but its urllib3 layer
serialises every request even under a thread pool — 90 concurrent per-day
calls that took under a second with plain `requests` took 20+ seconds
through elexonpy. Calling the REST API directly gets real concurrency and
drops that dependency.

The three data sources also behave differently over long ranges, discovered
by probing the live API:

- Settlement system prices (the imbalance price) can only be fetched one
  settlement date at a time, with no bulk/range endpoint, so a full ~10-year
  history would mean thousands of HTTP calls. Instead, callers are capped at
  `IMBALANCE_PRICE_MAX_DAYS` and every day in that window is fetched
  concurrently.
- Demand has a "daily" endpoint (INDOD) that looks ideal for long ranges, but
  it silently truncates results for older date ranges instead of erroring —
  an undocumented quirk, not something to build on. Instead, this module
  always fetches the reliable half-hourly endpoint (in `_DEMAND_CHUNK_DAYS`
  chunks, its actual per-call limit) and, for ranges longer than a few days,
  downsamples to a daily mean itself with pandas.
- Generation actually does auto-downsample sensibly for long ranges (half-
  hourly for short windows, hourly/daily as the range grows), so it's used
  as-is, just chunked to its `_GENERATION_CHUNK_DAYS` per-call limit.

Across all three, `EARLIEST_AVAILABLE_DATE` is the latest (i.e. most
restrictive) start date at which real data was found for any of them, so
an "all time" query returns a consistent window on every chart.
"""

from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
_TIMEOUT_SECONDS = 20

# Verified against the live API: demand's half-hourly endpoint is the most
# restrictive of the three, returning nothing before early March 2016.
EARLIEST_AVAILABLE_DATE = dt.date(2016, 3, 1)

# No bulk endpoint exists for settlement system prices, so this chart is
# capped to a window fetchable as same-request concurrent per-day calls.
IMBALANCE_PRICE_MAX_DAYS = 90

# /demand/outturn's actual per-call range limit.
_DEMAND_CHUNK_DAYS = 28
# Beyond this many days, demand is resampled to a daily mean rather than
# returned half-hourly, to keep chart point counts sane.
_DEMAND_HALF_HOURLY_MAX_DAYS = 3

# /generation/actual/per-type's actual per-call range limit (367 days, with
# a one-day safety margin).
_GENERATION_CHUNK_DAYS = 360

_CONCURRENT_WORKERS = 20


def _get(path: str, params: dict) -> dict:
    response = requests.get(f"{_BASE_URL}{path}", params=params, timeout=_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _date_chunks(start: dt.date, end: dt.date, max_days: int) -> list[tuple[dt.date, dt.date]]:
    """Splits [start, end] into consecutive inclusive chunks of at most `max_days`."""
    chunks = []
    chunk_start = start
    while chunk_start <= end:
        chunk_end = min(chunk_start + dt.timedelta(days=max_days - 1), end)
        chunks.append((chunk_start, chunk_end))
        chunk_start = chunk_end + dt.timedelta(days=1)
    return chunks


def _fetch_concurrently(fetch_one, items: list) -> list:
    """Runs `fetch_one` over `items` on a thread pool and flattens the results."""
    with ThreadPoolExecutor(max_workers=_CONCURRENT_WORKERS) as executor:
        results = executor.map(fetch_one, items)
    return [row for rows in results for row in rows]


def get_imbalance_price_history(start: dt.date, end: dt.date) -> list[dict]:
    """Settlement system buy/sell prices (the GB imbalance price) over [start, end]."""
    effective_start = max(start, end - dt.timedelta(days=IMBALANCE_PRICE_MAX_DAYS - 1))
    dates = [
        effective_start + dt.timedelta(days=i) for i in range((end - effective_start).days + 1)
    ]

    def fetch_day(settlement_date: dt.date) -> list[dict]:
        body = _get(f"/balancing/settlement/system-prices/{settlement_date.isoformat()}", {})
        return body["data"]

    records = _fetch_concurrently(fetch_day, dates)
    if not records:
        return []

    frame = pd.DataFrame.from_records(records).sort_values("startTime")
    return [
        {
            "timestamp": row.startTime,
            "settlement_period": int(row.settlementPeriod),
            "system_sell_price": row.systemSellPrice,
            "system_buy_price": row.systemBuyPrice,
            "net_imbalance_volume": row.netImbalanceVolume,
        }
        for row in frame.itertuples()
    ]


def get_demand_history(start: dt.date, end: dt.date) -> list[dict]:
    """National demand outturn (INDO/ITSDO) over [start, end].

    Half-hourly for short ranges; resampled to a daily mean (keeping both
    series) for anything longer than a few days.
    """
    chunks = _date_chunks(start, end, _DEMAND_CHUNK_DAYS)

    def fetch_chunk(chunk: tuple[dt.date, dt.date]) -> list[dict]:
        chunk_start, chunk_end = chunk
        body = _get(
            "/demand/outturn",
            {
                "settlementDateFrom": chunk_start.isoformat(),
                "settlementDateTo": chunk_end.isoformat(),
            },
        )
        return body["data"]

    records = _fetch_concurrently(fetch_chunk, chunks)
    if not records:
        return []

    frame = pd.DataFrame.from_records(records).sort_values("startTime")
    frame["startTime"] = pd.to_datetime(frame["startTime"])

    if (end - start).days > _DEMAND_HALF_HOURLY_MAX_DAYS:
        frame = (
            frame.set_index("startTime")[
                ["initialDemandOutturn", "initialTransmissionSystemDemandOutturn"]
            ]
            .resample("1D")
            .mean()
            .dropna(how="all")
            .reset_index()
        )

    return [
        {
            "timestamp": pd.Timestamp(row.startTime).isoformat(),
            "national_demand_mw": row.initialDemandOutturn,
            "transmission_system_demand_mw": row.initialTransmissionSystemDemandOutturn,
        }
        for row in frame.itertuples()
    ]


# Wind and solar are metered/reported near-real-time; the other fuel types
# (gas, nuclear, coal, biomass, hydro, "other") come from a dataset that lags
# real time by roughly 2-3 weeks. Until it catches up, every one of those
# fuel types reports exactly 0 MW rather than a missing row, which would
# otherwise render as "gas generation stopped" — obviously false. Rows for
# these fuel types beyond `_lagging_data_cutoff()` are dropped rather than
# shown as a fake zero; wind/solar rows for the same trailing period are
# kept, since they really are published that recently.
_NEAR_REAL_TIME_FUEL_TYPES = {"Solar", "Wind Onshore", "Wind Offshore"}

# How far back to look to find the lagging cutoff. Observed lag is ~2-3
# weeks; this gives a comfortable margin without scanning the full history.
_CUTOFF_LOOKBACK_DAYS = 45


def _lagging_data_cutoff() -> str | None:
    """Latest timestamp with real (non-zero) data for the lagging fuel types, if any."""
    today = dt.date.today()
    frm = dt.datetime.combine(
        today - dt.timedelta(days=_CUTOFF_LOOKBACK_DAYS), dt.time.min, tzinfo=dt.UTC
    )
    to = dt.datetime.combine(today + dt.timedelta(days=1), dt.time.min, tzinfo=dt.UTC)
    body = _get("/generation/actual/per-type", {"from": frm.isoformat(), "to": to.isoformat()})

    published_timestamps = [
        period["startTime"]
        for period in body["data"]
        for value in period["data"]
        if value["psrType"] not in _NEAR_REAL_TIME_FUEL_TYPES and value["quantity"] > 0
    ]
    return max(published_timestamps) if published_timestamps else None


def get_generation_mix_history(start: dt.date, end: dt.date) -> list[dict]:
    """Actual generation output over [start, end], broken down by fuel type (PSR type).

    Elexon auto-downsamples this endpoint's resolution to the requested
    range (half-hourly/hourly/daily), so no resampling is needed here. Any
    trailing settlement periods not yet published for the lagging fuel types
    (see `_NEAR_REAL_TIME_FUEL_TYPES`) are dropped rather than shown as zero.
    """
    chunks = _date_chunks(start, end, _GENERATION_CHUNK_DAYS)

    def fetch_chunk(chunk: tuple[dt.date, dt.date]) -> list[dict]:
        chunk_start, chunk_end = chunk
        chunk_from = dt.datetime.combine(chunk_start, dt.time.min, tzinfo=dt.UTC)
        chunk_to = dt.datetime.combine(chunk_end + dt.timedelta(days=1), dt.time.min, tzinfo=dt.UTC)
        body = _get(
            "/generation/actual/per-type",
            {"from": chunk_from.isoformat(), "to": chunk_to.isoformat()},
        )
        return body["data"]

    periods = _fetch_concurrently(fetch_chunk, chunks)
    records = [
        {
            "timestamp": period["startTime"],
            "fuel_type": value["psrType"],
            "quantity_mw": value["quantity"],
        }
        for period in periods
        for value in period["data"]
    ]

    cutoff = _lagging_data_cutoff() if end >= dt.date.today() - dt.timedelta(days=1) else None
    if cutoff is None:
        return records

    return [
        r
        for r in records
        if r["fuel_type"] in _NEAR_REAL_TIME_FUEL_TYPES or r["timestamp"] <= cutoff
    ]
