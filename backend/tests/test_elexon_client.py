import datetime as dt

from app.services import elexon_client


def test_date_chunks_splits_into_inclusive_windows_of_max_size() -> None:
    chunks = elexon_client._date_chunks(dt.date(2024, 1, 1), dt.date(2024, 1, 10), max_days=4)

    assert chunks == [
        (dt.date(2024, 1, 1), dt.date(2024, 1, 4)),
        (dt.date(2024, 1, 5), dt.date(2024, 1, 8)),
        (dt.date(2024, 1, 9), dt.date(2024, 1, 10)),
    ]


def test_date_chunks_returns_single_chunk_when_range_fits() -> None:
    chunks = elexon_client._date_chunks(dt.date(2024, 1, 1), dt.date(2024, 1, 1), max_days=28)

    assert chunks == [(dt.date(2024, 1, 1), dt.date(2024, 1, 1))]


def test_resample_rule_picks_native_daily_or_weekly_by_range_width() -> None:
    start = dt.date(2024, 1, 1)

    assert elexon_client._resample_rule(start, start + dt.timedelta(days=3)) is None
    assert elexon_client._resample_rule(start, start + dt.timedelta(days=4)) == "1D"
    assert elexon_client._resample_rule(start, start + dt.timedelta(days=366)) == "1D"
    assert elexon_client._resample_rule(start, start + dt.timedelta(days=367)) == "1W"


def test_imbalance_price_history_clamps_to_max_days(monkeypatch) -> None:
    calls: list[str] = []

    def fake_get(path: str, params: dict) -> dict:
        calls.append(path)
        return {"data": []}

    monkeypatch.setattr(elexon_client, "_get", fake_get)

    start = elexon_client.EARLIEST_AVAILABLE_DATE
    end = start + dt.timedelta(days=365)
    elexon_client.get_imbalance_price_history(start, end)

    # One call per day in the window, capped at IMBALANCE_PRICE_MAX_DAYS
    # regardless of how much wider the requested range was.
    assert len(calls) == elexon_client.IMBALANCE_PRICE_MAX_DAYS


def test_imbalance_price_history_resamples_to_daily_mean_for_wide_ranges(monkeypatch) -> None:
    def fake_get(path: str, params: dict) -> dict:
        settlement_date = path.rsplit("/", 1)[-1]
        day_start = dt.datetime.fromisoformat(settlement_date).replace(tzinfo=dt.UTC)
        return {
            "data": [
                {
                    "startTime": day_start.isoformat().replace("+00:00", "Z"),
                    "settlementPeriod": 1,
                    "systemSellPrice": 50.0,
                    "systemBuyPrice": 50.0,
                    "netImbalanceVolume": 10.0,
                },
                {
                    "startTime": (day_start + dt.timedelta(hours=12))
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "settlementPeriod": 25,
                    "systemSellPrice": 70.0,
                    "systemBuyPrice": 70.0,
                    "netImbalanceVolume": -10.0,
                },
            ]
        }

    monkeypatch.setattr(elexon_client, "_get", fake_get)

    end = dt.date(2024, 1, 10)
    start = end - dt.timedelta(days=9)  # 10-day range: above the daily threshold
    result = elexon_client.get_imbalance_price_history(start, end)

    assert len(result) == 10  # one row per day, not one per settlement period
    assert result[0]["settlement_period"] is None  # no longer meaningful once averaged
    assert result[0]["system_sell_price"] == 60.0  # mean of 50 and 70


def test_demand_history_stays_half_hourly_for_short_ranges(monkeypatch) -> None:
    def fake_get(path: str, params: dict) -> dict:
        return {
            "data": [
                {
                    "startTime": "2024-01-01T00:00:00Z",
                    "initialDemandOutturn": 20000,
                    "initialTransmissionSystemDemandOutturn": 21000,
                },
                {
                    "startTime": "2024-01-01T00:30:00Z",
                    "initialDemandOutturn": 21000,
                    "initialTransmissionSystemDemandOutturn": 22000,
                },
            ]
        }

    monkeypatch.setattr(elexon_client, "_get", fake_get)

    # A 1-day range fits in a single 28-day chunk, so `fake_get` is called once.
    result = elexon_client.get_demand_history(dt.date(2024, 1, 1), dt.date(2024, 1, 2))

    assert len(result) == 2
    assert result[0]["national_demand_mw"] == 20000


def test_demand_history_resamples_to_daily_mean_for_long_ranges(monkeypatch) -> None:
    def fake_get(path: str, params: dict) -> dict:
        # A 10-day range also fits in one 28-day chunk, so this fires once;
        # synthesise two half-hourly readings per day across the full window.
        chunk_start = dt.date.fromisoformat(params["settlementDateFrom"])
        chunk_end = dt.date.fromisoformat(params["settlementDateTo"])
        rows = []
        day = chunk_start
        while day <= chunk_end:
            day_start = dt.datetime.combine(day, dt.time.min, tzinfo=dt.UTC)
            rows.append(
                {
                    "startTime": day_start.isoformat().replace("+00:00", "Z"),
                    "initialDemandOutturn": 10000,
                    "initialTransmissionSystemDemandOutturn": 12000,
                }
            )
            rows.append(
                {
                    "startTime": (day_start + dt.timedelta(hours=12))
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "initialDemandOutturn": 20000,
                    "initialTransmissionSystemDemandOutturn": 24000,
                }
            )
            day += dt.timedelta(days=1)
        return {"data": rows}

    monkeypatch.setattr(elexon_client, "_get", fake_get)

    result = elexon_client.get_demand_history(dt.date(2024, 1, 1), dt.date(2024, 1, 10))

    # Resampled to one row per day, not one row per half-hourly reading.
    assert len(result) == 10
    assert result[0]["national_demand_mw"] == 15000  # mean of 10000 and 20000
    assert result[0]["transmission_system_demand_mw"] == 18000


def test_generation_mix_history_drops_unpublished_rows_for_lagging_fuel_types(
    monkeypatch,
) -> None:
    today = dt.date.today()
    cutoff_time = "2024-01-01T00:00:00Z"
    stale_time = "2024-01-01T00:30:00Z"
    call_log: list[dict] = []

    def fake_get(path: str, params: dict) -> dict:
        call_log.append(params)
        if len(call_log) == 1:
            # Main fetch for the requested range: gas genuinely reported at
            # cutoff_time, then 0 (i.e. not yet published) at stale_time.
            # Wind is reported at both, since it isn't affected by the lag.
            return {
                "data": [
                    {
                        "startTime": cutoff_time,
                        "data": [
                            {"psrType": "Fossil Gas", "quantity": 500.0},
                            {"psrType": "Wind Onshore", "quantity": 100.0},
                        ],
                    },
                    {
                        "startTime": stale_time,
                        "data": [
                            {"psrType": "Fossil Gas", "quantity": 0.0},
                            {"psrType": "Wind Onshore", "quantity": 110.0},
                        ],
                    },
                ]
            }
        # The separate cutoff-lookback call: gas is only ever non-zero at
        # cutoff_time within the lookback window.
        return {
            "data": [
                {"startTime": cutoff_time, "data": [{"psrType": "Fossil Gas", "quantity": 500.0}]},
                {"startTime": stale_time, "data": [{"psrType": "Fossil Gas", "quantity": 0.0}]},
            ]
        }

    monkeypatch.setattr(elexon_client, "_get", fake_get)

    result = elexon_client.get_generation_mix_history(today - dt.timedelta(days=1), today)

    gas_rows = [r for r in result if r["fuel_type"] == "Fossil Gas"]
    wind_rows = [r for r in result if r["fuel_type"] == "Wind Onshore"]
    assert [r["timestamp"] for r in gas_rows] == [cutoff_time]
    assert len(wind_rows) == 2  # wind/solar are kept even past the cutoff


def test_generation_mix_history_skips_cutoff_check_for_purely_historical_ranges(
    monkeypatch,
) -> None:
    calls: list[dict] = []

    def fake_get(path: str, params: dict) -> dict:
        calls.append(params)
        return {
            "data": [
                {"startTime": params["from"], "data": [{"psrType": "Fossil Gas", "quantity": 0.0}]}
            ]
        }

    monkeypatch.setattr(elexon_client, "_get", fake_get)

    elexon_client.get_generation_mix_history(dt.date(2018, 1, 1), dt.date(2018, 1, 2))

    # Only the main chunk fetch fires; no extra call to find a lagging cutoff.
    assert len(calls) == 1


def test_generation_mix_history_resamples_per_fuel_type_for_wide_ranges(monkeypatch) -> None:
    def fake_get(path: str, params: dict) -> dict:
        chunk_from = dt.datetime.fromisoformat(params["from"])
        chunk_to = dt.datetime.fromisoformat(params["to"])
        periods = []
        t = chunk_from
        while t < chunk_to:
            periods.append(
                {
                    "startTime": t.isoformat().replace("+00:00", "Z"),
                    "data": [
                        {"psrType": "Fossil Gas", "quantity": 100.0},
                        {"psrType": "Wind Onshore", "quantity": 10.0},
                    ],
                }
            )
            t += dt.timedelta(hours=12)
        return {"data": periods}

    monkeypatch.setattr(elexon_client, "_get", fake_get)

    end = dt.date(2024, 1, 10)
    start = end - dt.timedelta(days=9)  # 10-day range: above the daily threshold
    result = elexon_client.get_generation_mix_history(start, end)

    gas_rows = [r for r in result if r["fuel_type"] == "Fossil Gas"]
    wind_rows = [r for r in result if r["fuel_type"] == "Wind Onshore"]
    # One row per fuel type per day, not one per half-hourly reading.
    assert len(gas_rows) == 10
    assert len(wind_rows) == 10
    assert gas_rows[0]["quantity_mw"] == 100.0


def test_generation_mix_history_chunks_long_ranges(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_get(path: str, params: dict) -> dict:
        calls.append(params)
        return {
            "data": [
                {
                    "startTime": params["from"],
                    "data": [{"psrType": "Wind Onshore", "quantity": 100.0}],
                }
            ]
        }

    monkeypatch.setattr(elexon_client, "_get", fake_get)

    start = elexon_client.EARLIEST_AVAILABLE_DATE
    end = start + dt.timedelta(days=800)  # spans three 360-day chunks
    result = elexon_client.get_generation_mix_history(start, end)

    assert len(calls) == 3
    assert len(result) == 3
    assert all(row["fuel_type"] == "Wind Onshore" for row in result)
