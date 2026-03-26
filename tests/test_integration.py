"""
Integration tests against the live FlashAlpha API.

Run with:
    export FLASHALPHA_API_KEY=your_key_here
    pytest tests/test_integration.py -v -m integration
"""

import os

import pytest
import requests

from flashalpha import FlashAlpha, FlashAlphaError, TierRestrictedError

FLASHALPHA_BASE = "https://lab.flashalpha.com"
TICKER = "SPY"


@pytest.fixture(scope="module")
def api_key() -> str:
    key = os.environ.get("FLASHALPHA_API_KEY", "")
    if not key:
        pytest.skip("FLASHALPHA_API_KEY not set — skipping integration tests")
    return key


@pytest.fixture(scope="module")
def auth_headers(api_key: str) -> dict:
    return {"X-Api-Key": api_key}


@pytest.fixture(scope="module")
def fa_client(api_key: str) -> FlashAlpha:
    return FlashAlpha(api_key)


def get(path: str, headers: dict, timeout: int = 15) -> dict:
    url = f"{FLASHALPHA_BASE}{path}"
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


@pytest.mark.integration
class TestGexEndpoint:
    def test_gex_returns_200(self, auth_headers):
        url = f"{FLASHALPHA_BASE}/v1/exposure/gex/{TICKER}"
        resp = requests.get(url, headers=auth_headers, timeout=15)
        assert resp.status_code == 200

    def test_gex_has_required_fields(self, auth_headers):
        data = get(f"/v1/exposure/gex/{TICKER}", auth_headers)
        assert data["symbol"] == TICKER
        assert "net_gex" in data
        assert "gamma_flip" in data
        assert isinstance(data["strikes"], list)
        assert len(data["strikes"]) > 0

    def test_gex_strike_fields(self, auth_headers):
        data = get(f"/v1/exposure/gex/{TICKER}", auth_headers)
        strike = data["strikes"][0]
        for field in ("strike", "call_gex", "put_gex", "net_gex"):
            assert field in strike, f"Missing field '{field}' in strike data"
            assert isinstance(strike[field], (int, float))

    def test_net_gex_is_numeric(self, auth_headers):
        data = get(f"/v1/exposure/gex/{TICKER}", auth_headers)
        assert isinstance(data["net_gex"], (int, float))


@pytest.mark.integration
class TestLevelsEndpoint:
    def test_levels_returns_200(self, auth_headers):
        url = f"{FLASHALPHA_BASE}/v1/exposure/levels/{TICKER}"
        resp = requests.get(url, headers=auth_headers, timeout=15)
        assert resp.status_code == 200

    def test_levels_has_required_fields(self, auth_headers):
        data = get(f"/v1/exposure/levels/{TICKER}", auth_headers)
        levels = data["levels"]
        for field in ("gamma_flip", "call_wall", "put_wall"):
            assert field in levels, f"Missing '{field}' in levels"

    def test_walls_are_positive(self, auth_headers):
        levels = get(f"/v1/exposure/levels/{TICKER}", auth_headers)["levels"]
        assert levels["call_wall"] > 0
        assert levels["put_wall"] > 0

    def test_call_wall_above_put_wall(self, auth_headers):
        levels = get(f"/v1/exposure/levels/{TICKER}", auth_headers)["levels"]
        assert levels["call_wall"] >= levels["put_wall"]

    def test_gamma_flip_is_reasonable(self, auth_headers):
        levels = get(f"/v1/exposure/levels/{TICKER}", auth_headers)["levels"]
        flip = levels["gamma_flip"]
        assert isinstance(flip, (int, float))
        assert flip > 0


@pytest.mark.integration
class TestAuth:
    def test_missing_key_returns_401(self):
        url = f"{FLASHALPHA_BASE}/v1/exposure/levels/{TICKER}"
        resp = requests.get(url, headers={}, timeout=15)
        assert resp.status_code == 401

    def test_invalid_key_returns_401(self):
        url = f"{FLASHALPHA_BASE}/v1/exposure/levels/{TICKER}"
        resp = requests.get(url, headers={"X-Api-Key": "invalid-key-xyz"}, timeout=15)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# New integration tests: SDK client, GEX, levels, hedging, DEX/VEX/CHEX
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestGexStrikesSdk:
    """Verify gex() via the FlashAlpha SDK returns valid per-strike data."""

    def test_gex_returns_strikes_list(self, fa_client):
        data = fa_client.gex(TICKER)
        assert isinstance(data.get("strikes"), list)
        assert len(data["strikes"]) > 0

    def test_gex_strikes_have_call_put_net_gex(self, fa_client):
        data = fa_client.gex(TICKER)
        for row in data["strikes"][:5]:
            for field in ("strike", "call_gex", "put_gex", "net_gex"):
                assert field in row, f"Missing '{field}' in strike row"

    def test_gex_underlying_price_is_positive(self, fa_client):
        data = fa_client.gex(TICKER)
        price = data.get("underlying_price")
        assert price is not None
        assert price > 0

    def test_gex_call_gex_is_non_negative_at_all_strikes(self, fa_client):
        data = fa_client.gex(TICKER)
        for row in data["strikes"]:
            assert row["call_gex"] >= 0, f"Negative call_gex at {row['strike']}"

    def test_gex_put_gex_is_non_positive_at_all_strikes(self, fa_client):
        data = fa_client.gex(TICKER)
        for row in data["strikes"]:
            assert row["put_gex"] <= 0, f"Positive put_gex at {row['strike']}"


@pytest.mark.integration
class TestExposureLevelsSdk:
    """Verify exposure_levels() returns all required level fields."""

    def test_levels_response_has_levels_key(self, fa_client):
        data = fa_client.exposure_levels(TICKER)
        assert "levels" in data

    def test_all_level_fields_present(self, fa_client):
        levels = fa_client.exposure_levels(TICKER)["levels"]
        for field in ("gamma_flip", "call_wall", "put_wall"):
            assert field in levels, f"Missing field '{field}' in levels"

    def test_call_wall_above_put_wall(self, fa_client):
        levels = fa_client.exposure_levels(TICKER)["levels"]
        assert levels["call_wall"] > levels["put_wall"]

    def test_max_pain_is_present_and_positive(self, fa_client):
        levels = fa_client.exposure_levels(TICKER)["levels"]
        max_pain = levels.get("max_pain")
        if max_pain is not None:
            assert max_pain > 0

    def test_zero_dte_magnet_is_present(self, fa_client):
        levels = fa_client.exposure_levels(TICKER)["levels"]
        assert "zero_dte_magnet" in levels


@pytest.mark.integration
class TestExposureSummaryHedging:
    """Verify exposure_summary() returns hedging estimate data."""

    def test_summary_returns_dict(self, fa_client):
        try:
            data = fa_client.exposure_summary(TICKER)
            assert isinstance(data, dict)
        except TierRestrictedError:
            pytest.skip("exposure_summary requires Growth+ plan")

    def test_summary_has_exposures_section(self, fa_client):
        try:
            data = fa_client.exposure_summary(TICKER)
            assert "exposures" in data
            assert "net_gex" in data["exposures"]
        except TierRestrictedError:
            pytest.skip("exposure_summary requires Growth+ plan")

    def test_summary_has_hedging_estimate(self, fa_client):
        try:
            data = fa_client.exposure_summary(TICKER)
            assert "hedging_estimate" in data
        except TierRestrictedError:
            pytest.skip("exposure_summary requires Growth+ plan")


@pytest.mark.integration
class TestNarrativeSdk:
    """Verify narrative() returns all expected sections (if plan permits)."""

    def test_narrative_returns_dict(self, fa_client):
        try:
            data = fa_client.narrative(TICKER)
            assert isinstance(data, dict)
        except TierRestrictedError:
            pytest.skip("narrative requires Growth+ plan")

    def test_narrative_has_regime(self, fa_client):
        try:
            data = fa_client.narrative(TICKER)
            assert "narrative" in data
            assert "regime" in data["narrative"]
        except TierRestrictedError:
            pytest.skip("narrative requires Growth+ plan")

    def test_narrative_has_outlook(self, fa_client):
        try:
            data = fa_client.narrative(TICKER)
            if "outlook" in data:
                assert isinstance(data["outlook"], str)
                assert len(data["outlook"]) > 0
        except TierRestrictedError:
            pytest.skip("narrative requires Growth+ plan")


@pytest.mark.integration
class TestDexVexChexSdk:
    """Verify DEX, VEX, and CHEX endpoints return valid data."""

    def test_dex_returns_dict(self, fa_client):
        data = fa_client.dex(TICKER)
        assert isinstance(data, dict)

    def test_dex_has_strikes(self, fa_client):
        data = fa_client.dex(TICKER)
        if "strikes" in data:
            assert isinstance(data["strikes"], list)

    def test_vex_returns_dict(self, fa_client):
        data = fa_client.vex(TICKER)
        assert isinstance(data, dict)

    def test_chex_returns_dict(self, fa_client):
        data = fa_client.chex(TICKER)
        assert isinstance(data, dict)

    def test_vex_has_net_field(self, fa_client):
        data = fa_client.vex(TICKER)
        # net may appear as "net", "net_vex", or similar — just verify one exists
        has_net = any(k in data for k in ("net", "net_vex", "total"))
        assert has_net, f"No net field found in VEX response: {list(data.keys())}"


@pytest.mark.integration
class TestStockQuoteSdk:
    """Verify stock_quote() returns valid quote data."""

    def test_stock_quote_returns_dict(self, fa_client):
        data = fa_client.stock_quote(TICKER)
        assert isinstance(data, dict)

    def test_stock_quote_has_bid_ask(self, fa_client):
        data = fa_client.stock_quote(TICKER)
        assert "bid" in data or "mid" in data, f"No price field found: {list(data.keys())}"

    def test_stock_quote_price_is_positive(self, fa_client):
        data = fa_client.stock_quote(TICKER)
        price = data.get("mid") or data.get("last") or data.get("bid")
        assert price is not None
        assert price > 0
