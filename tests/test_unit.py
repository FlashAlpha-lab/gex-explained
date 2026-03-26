"""
tests/test_unit.py

Unit tests for the FlashAlpha SDK integration code in this repo.
All tests mock the API — no live key required.

Run with:
    pytest tests/test_unit.py -v
"""

import os
import sys
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Helpers to build mock API responses matching FlashAlpha schema
# ---------------------------------------------------------------------------

def make_gex_response(symbol: str = "SPY", net_gex: float = 5e9, gamma_flip: float = 585.0) -> dict:
    return {
        "symbol": symbol,
        "underlying_price": 590.0,
        "net_gex": net_gex,
        "net_gex_label": "Positive" if net_gex >= 0 else "Negative",
        "gamma_flip": gamma_flip,
        "strikes": [
            {
                "strike": 580.0,
                "call_gex": 0.0,
                "put_gex": -2_000_000.0,
                "net_gex": -2_000_000.0,
                "oi": 10000,
                "volume": 3000,
            },
            {
                "strike": 590.0,
                "call_gex": 8_000_000.0,
                "put_gex": -1_000_000.0,
                "net_gex": 7_000_000.0,
                "oi": 25000,
                "volume": 8000,
            },
            {
                "strike": 600.0,
                "call_gex": 12_000_000.0,
                "put_gex": 0.0,
                "net_gex": 12_000_000.0,
                "oi": 30000,
                "volume": 12000,
            },
        ],
    }


def make_levels_response(symbol: str = "SPY") -> dict:
    return {
        "symbol": symbol,
        "levels": {
            "gamma_flip":      585.50,
            "call_wall":       600.0,
            "put_wall":        570.0,
            "max_pain":        588.0,
            "highest_oi_strike": 590.0,
            "zero_dte_magnet": 589.0,
        },
    }


def make_exposure_summary_response(symbol: str = "SPY") -> dict:
    return {
        "symbol": symbol,
        "gex": {
            "net_gex": 5_200_000_000.0,
            "net_gex_label": "Positive",
        },
        "hedging": {
            "up_1pct": {
                "shares_to_hedge": -450000,
                "direction": "sell",
                "notional_usd": -266_550_000.0,
            },
            "down_1pct": {
                "shares_to_hedge": 450000,
                "direction": "buy",
                "notional_usd": 266_550_000.0,
            },
        },
    }


def make_narrative_response(symbol: str = "SPY") -> dict:
    return {
        "symbol": symbol,
        "regime": "Positive gamma — dealers stabilizing, mean-reversion expected.",
        "gex_change": "GEX increased 8% week-over-week — positioning strengthening.",
        "levels": "Gamma flip at 585.50. Call wall 600, put wall 570.",
        "flow": "Net call buying with call/put ratio above 1.2.",
        "vanna": "Positive vanna — IV decline creates dealer selling pressure.",
        "charm": "Negative charm into Friday close — dealers will sell.",
        "zero_dte": "0DTE magnet at 589. Intraday regime: positive gamma.",
        "outlook": "Bias higher toward 600 call wall while price holds above 585.50 gamma flip.",
    }


def make_dex_response(symbol: str = "SPY") -> dict:
    return {
        "symbol": symbol,
        "net": -1_200_000_000.0,
        "strikes": [
            {"strike": 580.0, "exposure": -400_000_000.0},
            {"strike": 590.0, "exposure": -500_000_000.0},
            {"strike": 600.0, "exposure": -300_000_000.0},
        ],
    }


def make_vex_response(symbol: str = "SPY") -> dict:
    return {
        "symbol": symbol,
        "net": 800_000_000.0,
        "strikes": [
            {"strike": 580.0, "exposure": 200_000_000.0},
            {"strike": 590.0, "exposure": 350_000_000.0},
            {"strike": 600.0, "exposure": 250_000_000.0},
        ],
    }


def make_chex_response(symbol: str = "SPY") -> dict:
    return {
        "symbol": symbol,
        "net": -300_000_000.0,
        "strikes": [
            {"strike": 580.0, "exposure": -100_000_000.0},
            {"strike": 590.0, "exposure": -120_000_000.0},
            {"strike": 600.0, "exposure": -80_000_000.0},
        ],
    }


def make_stock_quote_response(symbol: str = "SPY") -> dict:
    return {
        "symbol": symbol,
        "bid":  589.50,
        "ask":  589.55,
        "mid":  589.525,
        "last": 589.52,
    }


# ---------------------------------------------------------------------------
# Tests: GEX response parsing
# ---------------------------------------------------------------------------

class TestGexResponseParsing:
    """Verify that the gex() response shape is parsed correctly."""

    def test_gex_has_symbol(self):
        resp = make_gex_response("SPY")
        assert resp["symbol"] == "SPY"

    def test_gex_has_net_gex(self):
        resp = make_gex_response(net_gex=5e9)
        assert resp["net_gex"] == 5e9

    def test_gex_has_strikes_list(self):
        resp = make_gex_response()
        assert isinstance(resp["strikes"], list)
        assert len(resp["strikes"]) > 0

    def test_gex_strike_has_required_fields(self):
        resp = make_gex_response()
        for strike in resp["strikes"]:
            for field in ("strike", "call_gex", "put_gex", "net_gex"):
                assert field in strike, f"Missing field '{field}' in strike row"

    def test_gex_positive_net_gex_label(self):
        resp = make_gex_response(net_gex=1e9)
        assert resp["net_gex_label"] == "Positive"

    def test_gex_negative_net_gex_label(self):
        resp = make_gex_response(net_gex=-1e9)
        assert resp["net_gex_label"] == "Negative"

    def test_gex_gamma_flip_is_float(self):
        resp = make_gex_response(gamma_flip=585.5)
        assert isinstance(resp["gamma_flip"], float)
        assert resp["gamma_flip"] == 585.5

    def test_gex_call_gex_is_non_negative(self):
        """Call GEX should be >= 0 at every strike."""
        resp = make_gex_response()
        for row in resp["strikes"]:
            assert row["call_gex"] >= 0, f"Call GEX negative at {row['strike']}"

    def test_gex_put_gex_is_non_positive(self):
        """Put GEX should be <= 0 at every strike."""
        resp = make_gex_response()
        for row in resp["strikes"]:
            assert row["put_gex"] <= 0, f"Put GEX positive at {row['strike']}"

    def test_gex_net_is_sum_of_call_and_put(self):
        resp = make_gex_response()
        for row in resp["strikes"]:
            expected = row["call_gex"] + row["put_gex"]
            assert abs(row["net_gex"] - expected) < 1.0, (
                f"net_gex mismatch at {row['strike']}: "
                f"expected {expected}, got {row['net_gex']}"
            )


# ---------------------------------------------------------------------------
# Tests: exposure_levels response parsing
# ---------------------------------------------------------------------------

class TestExposureLevelsParsing:
    """Verify that the exposure_levels() response shape is parsed correctly."""

    def test_levels_response_has_levels_key(self):
        resp = make_levels_response()
        assert "levels" in resp

    def test_levels_has_gamma_flip(self):
        levels = make_levels_response()["levels"]
        assert "gamma_flip" in levels
        assert isinstance(levels["gamma_flip"], float)

    def test_levels_has_call_wall(self):
        levels = make_levels_response()["levels"]
        assert "call_wall" in levels
        assert levels["call_wall"] > 0

    def test_levels_has_put_wall(self):
        levels = make_levels_response()["levels"]
        assert "put_wall" in levels
        assert levels["put_wall"] > 0

    def test_call_wall_above_put_wall(self):
        levels = make_levels_response()["levels"]
        assert levels["call_wall"] > levels["put_wall"]

    def test_levels_has_max_pain(self):
        levels = make_levels_response()["levels"]
        assert "max_pain" in levels

    def test_levels_has_zero_dte_magnet(self):
        levels = make_levels_response()["levels"]
        assert "zero_dte_magnet" in levels

    def test_range_width_is_positive(self):
        levels = make_levels_response()["levels"]
        width = levels["call_wall"] - levels["put_wall"]
        assert width > 0


# ---------------------------------------------------------------------------
# Tests: exposure_summary hedging estimates
# ---------------------------------------------------------------------------

class TestExposureSummaryHedging:
    """Verify the hedging estimate section of exposure_summary()."""

    def test_summary_has_hedging_key(self):
        resp = make_exposure_summary_response()
        assert "hedging" in resp

    def test_hedging_has_up_1pct(self):
        hedging = make_exposure_summary_response()["hedging"]
        assert "up_1pct" in hedging

    def test_hedging_has_down_1pct(self):
        hedging = make_exposure_summary_response()["hedging"]
        assert "down_1pct" in hedging

    def test_up_1pct_has_shares_direction_notional(self):
        up = make_exposure_summary_response()["hedging"]["up_1pct"]
        for field in ("shares_to_hedge", "direction", "notional_usd"):
            assert field in up, f"Missing '{field}' in up_1pct hedging"

    def test_positive_gamma_up_direction_is_sell(self):
        """In a positive gamma regime, dealers sell on up moves."""
        up = make_exposure_summary_response()["hedging"]["up_1pct"]
        assert up["direction"] == "sell"

    def test_positive_gamma_down_direction_is_buy(self):
        """In a positive gamma regime, dealers buy on down moves."""
        dn = make_exposure_summary_response()["hedging"]["down_1pct"]
        assert dn["direction"] == "buy"

    def test_notional_is_numeric(self):
        hedging = make_exposure_summary_response()["hedging"]
        assert isinstance(hedging["up_1pct"]["notional_usd"], (int, float))
        assert isinstance(hedging["down_1pct"]["notional_usd"], (int, float))


# ---------------------------------------------------------------------------
# Tests: narrative response sections
# ---------------------------------------------------------------------------

class TestNarrativeResponse:
    """Verify the narrative() response contains all expected sections."""

    EXPECTED_KEYS = ["regime", "gex_change", "levels", "flow", "vanna", "charm", "zero_dte", "outlook"]

    def test_narrative_has_all_sections(self):
        resp = make_narrative_response()
        for key in self.EXPECTED_KEYS:
            assert key in resp, f"Missing narrative section: '{key}'"

    def test_narrative_sections_are_strings(self):
        resp = make_narrative_response()
        for key in self.EXPECTED_KEYS:
            assert isinstance(resp[key], str), f"Narrative section '{key}' is not a string"

    def test_narrative_regime_is_not_empty(self):
        resp = make_narrative_response()
        assert len(resp["regime"]) > 0

    def test_narrative_outlook_is_not_empty(self):
        resp = make_narrative_response()
        assert len(resp["outlook"]) > 0


# ---------------------------------------------------------------------------
# Tests: DEX / VEX / CHEX responses
# ---------------------------------------------------------------------------

class TestDexVexChexResponses:
    """Verify the shape of DEX, VEX, and CHEX responses."""

    def test_dex_has_net(self):
        resp = make_dex_response()
        assert "net" in resp
        assert isinstance(resp["net"], (int, float))

    def test_vex_has_net(self):
        resp = make_vex_response()
        assert "net" in resp
        assert isinstance(resp["net"], (int, float))

    def test_chex_has_net(self):
        resp = make_chex_response()
        assert "net" in resp
        assert isinstance(resp["net"], (int, float))

    def test_dex_net_is_negative_in_positive_gamma_regime(self):
        """Dealers are typically net short delta in a positive gamma regime."""
        resp = make_dex_response()
        assert resp["net"] < 0

    def test_vex_has_strikes(self):
        resp = make_vex_response()
        assert isinstance(resp["strikes"], list)
        assert len(resp["strikes"]) > 0

    def test_chex_strikes_have_exposure_field(self):
        resp = make_chex_response()
        for row in resp["strikes"]:
            assert "exposure" in row, "Strike row missing 'exposure' field"
            assert isinstance(row["exposure"], (int, float))

    def test_vex_positive_net(self):
        resp = make_vex_response()
        assert resp["net"] > 0


# ---------------------------------------------------------------------------
# Tests: stock_quote response
# ---------------------------------------------------------------------------

class TestStockQuoteResponse:
    def test_quote_has_bid_ask_mid(self):
        resp = make_stock_quote_response()
        for field in ("bid", "ask", "mid"):
            assert field in resp

    def test_mid_is_between_bid_and_ask(self):
        resp = make_stock_quote_response()
        assert resp["bid"] <= resp["mid"] <= resp["ask"]


# ---------------------------------------------------------------------------
# Tests: FlashAlpha client error handling (mocked)
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Test that the SDK raises the correct exception types."""

    def test_401_raises_authentication_error(self):
        from flashalpha import FlashAlpha, AuthenticationError

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid API key"}

        fa = FlashAlpha("bad-key")
        with patch.object(fa._session, "get", return_value=mock_response):
            with pytest.raises(AuthenticationError):
                fa.gex("SPY")

    def test_403_raises_tier_restricted_error(self):
        from flashalpha import FlashAlpha, TierRestrictedError

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "message": "Upgrade required",
            "current_plan": "free",
            "required_plan": "growth",
        }

        fa = FlashAlpha("free-key")
        with patch.object(fa._session, "get", return_value=mock_response):
            with pytest.raises(TierRestrictedError):
                fa.narrative("SPY")

    def test_404_raises_not_found_error(self):
        from flashalpha import FlashAlpha, NotFoundError

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Symbol not found"}

        fa = FlashAlpha("valid-key")
        with patch.object(fa._session, "get", return_value=mock_response):
            with pytest.raises(NotFoundError):
                fa.gex("NOTREAL")

    def test_429_raises_rate_limit_error(self):
        from flashalpha import FlashAlpha, RateLimitError

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_response.headers = {"Retry-After": "30"}

        fa = FlashAlpha("valid-key")
        with patch.object(fa._session, "get", return_value=mock_response):
            with pytest.raises(RateLimitError):
                fa.gex("SPY")

    def test_500_raises_server_error(self):
        from flashalpha import FlashAlpha, ServerError

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}

        fa = FlashAlpha("valid-key")
        with patch.object(fa._session, "get", return_value=mock_response):
            with pytest.raises(ServerError):
                fa.gex("SPY")

    def test_200_returns_dict(self):
        from flashalpha import FlashAlpha

        gex_data = make_gex_response()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = gex_data

        fa = FlashAlpha("valid-key")
        with patch.object(fa._session, "get", return_value=mock_response):
            result = fa.gex("SPY")
        assert result["symbol"] == "SPY"
        assert result["net_gex"] == gex_data["net_gex"]
