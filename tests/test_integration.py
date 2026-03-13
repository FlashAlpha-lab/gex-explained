"""
tests/test_integration.py

Integration tests against the live FlashAlpha API.

These tests require a valid FLASHALPHA_API_KEY environment variable.
If the variable is not set, all tests in this file are skipped automatically.

Run with:
    export FLASHALPHA_API_KEY=your_key_here
    pytest tests/test_integration.py -v -m integration

API reference:
    Base URL : https://lab.flashalpha.com
    Auth     : X-Api-Key: <your_key>
"""

import os

import pytest
import requests

FLASHALPHA_BASE = "https://lab.flashalpha.com"
TICKER = "SPY"

# ---------------------------------------------------------------------------
# Shared fixture: skip if no API key
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def api_key() -> str:
    key = os.environ.get("FLASHALPHA_API_KEY", "")
    if not key:
        pytest.skip("FLASHALPHA_API_KEY not set — skipping integration tests")
    return key


@pytest.fixture(scope="module")
def auth_headers(api_key: str) -> dict:
    return {"X-Api-Key": api_key}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get(path: str, headers: dict, timeout: int = 15) -> dict:
    url = f"{FLASHALPHA_BASE}{path}"
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# GEX endpoint: /gex/{ticker}
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestGexEndpoint:
    def test_gex_returns_200(self, auth_headers):
        url = f"{FLASHALPHA_BASE}/gex/{TICKER}"
        resp = requests.get(url, headers=auth_headers, timeout=15)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_gex_response_is_json(self, auth_headers):
        data = get(f"/gex/{TICKER}", auth_headers)
        assert isinstance(data, (dict, list)), f"Expected dict or list, got {type(data)}"

    def test_gex_contains_strike_data(self, auth_headers):
        data = get(f"/gex/{TICKER}", auth_headers)
        # Accept either a dict (keyed by strike) or a list of strike records
        assert len(data) > 0, "GEX response is empty"

    def test_gex_values_are_numeric(self, auth_headers):
        data = get(f"/gex/{TICKER}", auth_headers)
        if isinstance(data, dict):
            for key, val in data.items():
                assert isinstance(val, (int, float)), (
                    f"GEX value at strike {key} is not numeric: {val!r}"
                )
        elif isinstance(data, list):
            for item in data:
                assert "gex" in item or "net_gex" in item, (
                    f"GEX list item missing gex field: {item}"
                )


# ---------------------------------------------------------------------------
# Levels endpoint: /gex/{ticker}/levels
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestLevelsEndpoint:
    def test_levels_returns_200(self, auth_headers):
        url = f"{FLASHALPHA_BASE}/gex/{TICKER}/levels"
        resp = requests.get(url, headers=auth_headers, timeout=15)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_levels_contains_call_wall(self, auth_headers):
        data = get(f"/gex/{TICKER}/levels", auth_headers)
        assert "call_wall" in data, f"'call_wall' missing from levels response: {data}"

    def test_levels_contains_put_wall(self, auth_headers):
        data = get(f"/gex/{TICKER}/levels", auth_headers)
        assert "put_wall" in data, f"'put_wall' missing from levels response: {data}"

    def test_levels_contains_gamma_flip(self, auth_headers):
        data = get(f"/gex/{TICKER}/levels", auth_headers)
        assert "gamma_flip" in data, f"'gamma_flip' missing from levels response: {data}"

    def test_gamma_flip_is_between_put_wall_and_call_wall(self, auth_headers):
        """
        The gamma flip should be a reasonable price level — between the put wall
        and call wall (not necessarily strictly between, but within striking distance).
        """
        data = get(f"/gex/{TICKER}/levels", auth_headers)
        flip = data.get("gamma_flip")
        put_wall = data.get("put_wall")
        call_wall = data.get("call_wall")

        if flip is None:
            pytest.skip("gamma_flip is None — no flip in current strike range")

        assert isinstance(flip, (int, float)), f"gamma_flip is not numeric: {flip!r}"
        assert isinstance(put_wall, (int, float)), f"put_wall is not numeric: {put_wall!r}"
        assert isinstance(call_wall, (int, float)), f"call_wall is not numeric: {call_wall!r}"

        lower = min(put_wall, call_wall)
        upper = max(put_wall, call_wall)

        # Allow 10% buffer outside the put/call wall range
        buffer = (upper - lower) * 0.10
        assert lower - buffer <= flip <= upper + buffer, (
            f"gamma_flip {flip} is not near the range [{lower}, {upper}]"
        )

    def test_call_wall_is_positive_number(self, auth_headers):
        data = get(f"/gex/{TICKER}/levels", auth_headers)
        call_wall = data["call_wall"]
        assert isinstance(call_wall, (int, float))
        assert call_wall > 0

    def test_put_wall_is_positive_number(self, auth_headers):
        data = get(f"/gex/{TICKER}/levels", auth_headers)
        put_wall = data["put_wall"]
        assert isinstance(put_wall, (int, float))
        assert put_wall > 0

    def test_call_wall_is_above_put_wall(self, auth_headers):
        """Call wall should be at a higher strike than put wall in normal markets."""
        data = get(f"/gex/{TICKER}/levels", auth_headers)
        assert data["call_wall"] > data["put_wall"], (
            f"call_wall ({data['call_wall']}) should be above put_wall ({data['put_wall']})"
        )


# ---------------------------------------------------------------------------
# Auth: invalid key should return 401 or 403
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAuth:
    def test_missing_key_returns_error(self):
        url = f"{FLASHALPHA_BASE}/gex/{TICKER}/levels"
        resp = requests.get(url, headers={}, timeout=15)
        assert resp.status_code in (401, 403), (
            f"Expected 401 or 403 for missing key, got {resp.status_code}"
        )

    def test_invalid_key_returns_error(self):
        url = f"{FLASHALPHA_BASE}/gex/{TICKER}/levels"
        resp = requests.get(url, headers={"X-Api-Key": "invalid-key-xyz"}, timeout=15)
        assert resp.status_code in (401, 403), (
            f"Expected 401 or 403 for invalid key, got {resp.status_code}"
        )
