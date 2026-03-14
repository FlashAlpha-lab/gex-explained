"""
Integration tests against the live FlashAlpha API.

Run with:
    export FLASHALPHA_API_KEY=your_key_here
    pytest tests/test_integration.py -v -m integration
"""

import os

import pytest
import requests

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
