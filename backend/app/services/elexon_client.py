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
  chunks, its actual per-call limit).
- Generation does auto-downsample somewhat for long ranges, but
  inconsistently across chunk boundaries, so it's chunked to its
  `_GENERATION_CHUNK_DAYS` per-call limit and then resampled the same way
  as the other two.

Across all three, `EARLIEST_AVAILABLE_DATE` is the latest (i.e. most
restrictive) start date at which real data was found for any of them, so
an "all time" query returns a consistent window on every chart. And all
three share `_resample_rule`: native resolution for short ranges, a daily
mean beyond `_NATIVE_RESOLUTION_MAX_DAYS`, a weekly mean beyond
`_WEEKLY_RESOLUTION_MIN_DAYS` — so a year-or-wider chart stays legible
instead of being thousands of noisy points.

A fourth source, day-ahead prices, was added the same way: probed live and
chunked to its actual `_MARKET_INDEX_CHUNK_DAYS` per-call limit. Its market
index data (MID) reports one row per index data provider (APX, N2EX) per
settlement period; N2EX has reported zero volume for every period checked
(recent and historical), so a naive average would be pulled towards zero
half the time. Rows are combined with a volume weighted average instead,
which both handles that (a zero-volume row can't move the price) and is the
methodologically correct way to combine two venues' prices anyway.
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

# /generation/actual/per-type's actual per-call range limit (367 days, with
# a one-day safety margin).
_GENERATION_CHUNK_DAYS = 360

# /balancing/pricing/market-index's actual per-call range limit.
_MARKET_INDEX_CHUNK_DAYS = 7

_CONCURRENT_WORKERS = 20

# Chart resolution, based on how wide the selected range is. Ranges above
# `_NATIVE_RESOLUTION_MAX_DAYS` are resampled to a daily mean, and above
# `_WEEKLY_RESOLUTION_MIN_DAYS` to a weekly mean, so a multi-year chart isn't
# thousands of noisy half-hourly points. All three endpoints share this.
_NATIVE_RESOLUTION_MAX_DAYS = 3
_WEEKLY_RESOLUTION_MIN_DAYS = 366


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


def _resample_rule(start: dt.date, end: dt.date) -> str | None:
    """Pandas resample rule for a range this wide, or None to keep native resolution."""
    days = (end - start).days
    if days > _WEEKLY_RESOLUTION_MIN_DAYS:
        return "1W"
    if days > _NATIVE_RESOLUTION_MAX_DAYS:
        return "1D"
    return None


def get_imbalance_price_history(start: dt.date, end: dt.date) -> list[dict]:
    """Settlement system buy/sell prices (the GB imbalance price) over [start, end].

    Resampled to a daily or weekly mean for wider ranges, same as demand and
    generation (see `_resample_rule`); the settlement period number stops
    meaning anything once periods are averaged together, so it's dropped then.
    """
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
    frame["startTime"] = pd.to_datetime(frame["startTime"])

    rule = _resample_rule(effective_start, end)
    if rule:
        frame = (
            frame.set_index("startTime")[
                ["systemSellPrice", "systemBuyPrice", "netImbalanceVolume"]
            ]
            .resample(rule)
            .mean()
            .dropna(how="all")
            .reset_index()
        )
        return [
            {
                "timestamp": pd.Timestamp(row.startTime).isoformat(),
                "settlement_period": None,
                "system_sell_price": row.systemSellPrice,
                "system_buy_price": row.systemBuyPrice,
                "net_imbalance_volume": row.netImbalanceVolume,
            }
            for row in frame.itertuples()
        ]

    return [
        {
            "timestamp": pd.Timestamp(row.startTime).isoformat(),
            "settlement_period": int(row.settlementPeriod),
            "system_sell_price": row.systemSellPrice,
            "system_buy_price": row.systemBuyPrice,
            "net_imbalance_volume": row.netImbalanceVolume,
        }
        for row in frame.itertuples()
    ]


def get_demand_history(start: dt.date, end: dt.date) -> list[dict]:
    """National demand outturn (INDO/ITSDO) over [start, end].

    Half-hourly for short ranges; resampled to a daily or weekly mean
    (keeping both series) for wider ones — see `_resample_rule`.
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

    rule = _resample_rule(start, end)
    if rule:
        frame = (
            frame.set_index("startTime")[
                ["initialDemandOutturn", "initialTransmissionSystemDemandOutturn"]
            ]
            .resample(rule)
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

    Elexon auto-downsamples this endpoint's resolution somewhat already, but
    inconsistently across chunk boundaries, so it's resampled again here to
    a daily/weekly mean for wider ranges (see `_resample_rule`) for a
    consistent resolution throughout. Any trailing settlement periods not
    yet published for the lagging fuel types (see `_NEAR_REAL_TIME_FUEL_TYPES`)
    are dropped — before resampling, so they don't drag down the average —
    rather than shown as zero.
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
    if cutoff is not None:
        records = [
            r
            for r in records
            if r["fuel_type"] in _NEAR_REAL_TIME_FUEL_TYPES or r["timestamp"] <= cutoff
        ]

    rule = _resample_rule(start, end)
    if not rule or not records:
        return records

    frame = pd.DataFrame.from_records(records)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    resampled = (
        frame.set_index("timestamp")
        .groupby("fuel_type")["quantity_mw"]
        .resample(rule)
        .mean()
        .dropna()
        .reset_index()
    )
    return [
        {
            "timestamp": row.timestamp.isoformat(),
            "fuel_type": row.fuel_type,
            "quantity_mw": row.quantity_mw,
        }
        for row in resampled.itertuples()
    ]


def _fetch_day_ahead_records(start: dt.date, end: dt.date) -> list[dict]:
    """Raw market index data (MID) rows over [start, end]: one per index data
    provider (APX, N2EX) per settlement period, chunked to the endpoint's
    per-call range limit."""
    chunks = _date_chunks(start, end, _MARKET_INDEX_CHUNK_DAYS)

    def fetch_chunk(chunk: tuple[dt.date, dt.date]) -> list[dict]:
        chunk_start, chunk_end = chunk
        chunk_from = dt.datetime.combine(chunk_start, dt.time.min, tzinfo=dt.UTC)
        chunk_to = dt.datetime.combine(chunk_end + dt.timedelta(days=1), dt.time.min, tzinfo=dt.UTC)
        body = _get(
            "/balancing/pricing/market-index",
            {"from": chunk_from.isoformat(), "to": chunk_to.isoformat()},
        )
        return body["data"]

    return _fetch_concurrently(fetch_chunk, chunks)


def _volume_weighted_price_by_period(records: list[dict]) -> pd.DataFrame:
    """Combines per-provider MID rows into one volume weighted price per
    settlement period, dropping the zero-volume rows a quiet provider
    (historically N2EX) reports rather than letting them drag the average
    towards zero."""
    frame = pd.DataFrame.from_records(records)
    frame = frame[frame["volume"] > 0]
    if frame.empty:
        return frame

    frame["startTime"] = pd.to_datetime(frame["startTime"])
    frame["weightedPrice"] = frame["price"] * frame["volume"]
    return (
        frame.groupby(["startTime", "settlementPeriod"])
        .agg(weightedPrice=("weightedPrice", "sum"), volume=("volume", "sum"))
        .assign(price=lambda f: f.weightedPrice / f.volume)
        .reset_index()
        .sort_values("startTime")
    )


def get_day_ahead_price_history(start: dt.date, end: dt.date) -> list[dict]:
    """GB day-ahead price over [start, end]: the volume weighted average of
    the market index data (MID) providers (APX, N2EX) for each settlement
    period — the closest free proxy for the day-ahead auction clearing
    price, since Elexon doesn't publish the exchanges' own auction results.

    Resampled to a daily or weekly mean for wider ranges, same as the other
    three data sources (see `_resample_rule`).
    """
    records = _fetch_day_ahead_records(start, end)
    if not records:
        return []

    frame = _volume_weighted_price_by_period(records)
    if frame.empty:
        return []

    rule = _resample_rule(start, end)
    if rule:
        frame = frame.set_index("startTime")[["price"]].resample(rule).mean().dropna().reset_index()
        return [
            {
                "timestamp": pd.Timestamp(row.startTime).isoformat(),
                "settlement_period": None,
                "price": row.price,
            }
            for row in frame.itertuples()
        ]

    return [
        {
            "timestamp": pd.Timestamp(row.startTime).isoformat(),
            "settlement_period": int(row.settlementPeriod),
            "price": row.price,
        }
        for row in frame.itertuples()
    ]


def get_day_ahead_price_profile(start: dt.date, end: dt.date) -> list[dict]:
    """Average day-ahead price by settlement period (1-48) across [start, end]
    — the typical daily shape (cheap overnight, an evening peak) that a VPP
    schedules its charge/discharge cycle around. `std_price` is the spread
    across the days in range, a rough read on how reliable that shape is.
    """
    records = _fetch_day_ahead_records(start, end)
    if not records:
        return []

    frame = _volume_weighted_price_by_period(records)
    if frame.empty:
        return []

    stats = (
        frame.groupby("settlementPeriod")["price"]
        .agg(mean_price="mean", std_price="std", sample_count="count")
        .reset_index()
    )
    return [
        {
            "settlement_period": int(row.settlementPeriod),
            "mean_price": row.mean_price,
            "std_price": 0.0 if pd.isna(row.std_price) else row.std_price,
            "sample_count": int(row.sample_count),
        }
        for row in stats.itertuples()
    ]
