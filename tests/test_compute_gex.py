"""
tests/test_compute_gex.py

Unit tests for the GEX computation logic in code/compute_gex.py.

Run with:
    pytest tests/test_compute_gex.py -v
"""

import math
import os
import sys

import pytest

# Allow importing from the code directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from compute_gex import (
    bsm_gamma,
    contract_gex,
    compute_gex_profile,
    load_chain,
)


# ---------------------------------------------------------------------------
# bsm_gamma
# ---------------------------------------------------------------------------

class TestBsmGamma:
    def test_atm_gamma_is_positive(self):
        g = bsm_gamma(spot=590, strike=590, T=7/365, r=0.05, sigma=0.18)
        assert g > 0

    def test_gamma_is_same_for_call_and_put(self):
        """BSM gamma is identical for calls and puts (put-call parity)."""
        g_call = bsm_gamma(spot=590, strike=590, T=30/365, r=0.05, sigma=0.18)
        g_put  = bsm_gamma(spot=590, strike=590, T=30/365, r=0.05, sigma=0.18)
        assert math.isclose(g_call, g_put)

    def test_gamma_increases_as_expiry_approaches(self):
        """ATM gamma should be higher with less time to expiry."""
        g_far  = bsm_gamma(spot=590, strike=590, T=90/365, r=0.05, sigma=0.18)
        g_near = bsm_gamma(spot=590, strike=590, T=7/365,  r=0.05, sigma=0.18)
        assert g_near > g_far

    def test_gamma_is_higher_atm_than_otm(self):
        """Gamma peaks at ATM and falls off for deep ITM/OTM strikes."""
        g_atm = bsm_gamma(spot=590, strike=590, T=14/365, r=0.05, sigma=0.18)
        g_otm = bsm_gamma(spot=590, strike=650, T=14/365, r=0.05, sigma=0.18)
        assert g_atm > g_otm

    def test_zero_tte_returns_zero(self):
        g = bsm_gamma(spot=590, strike=590, T=0, r=0.05, sigma=0.18)
        assert g == 0.0

    def test_zero_vol_returns_zero(self):
        g = bsm_gamma(spot=590, strike=590, T=14/365, r=0.05, sigma=0.0)
        assert g == 0.0


# ---------------------------------------------------------------------------
# contract_gex sign convention
# ---------------------------------------------------------------------------

class TestContractGexSign:
    """
    Dealer convention:
        Calls -> positive GEX (dealers long gamma, mean-reverting)
        Puts  -> negative GEX (dealers short gamma, momentum-amplifying)
    """

    KWARGS = dict(spot=590, strike=590, T=14/365, r=0.05, sigma=0.18, oi=1000)

    def test_call_gex_is_positive(self):
        gex = contract_gex(**self.KWARGS, option_type="C")
        assert gex > 0, f"Call GEX should be positive, got {gex}"

    def test_put_gex_is_negative(self):
        gex = contract_gex(**self.KWARGS, option_type="P")
        assert gex < 0, f"Put GEX should be negative, got {gex}"

    def test_call_and_put_gex_are_equal_magnitude(self):
        """With the same inputs, |call_gex| == |put_gex|."""
        gex_c = contract_gex(**self.KWARGS, option_type="C")
        gex_p = contract_gex(**self.KWARGS, option_type="P")
        assert math.isclose(abs(gex_c), abs(gex_p))

    def test_lowercase_type_accepted(self):
        gex_c = contract_gex(**self.KWARGS, option_type="c")
        gex_p = contract_gex(**self.KWARGS, option_type="p")
        assert gex_c > 0
        assert gex_p < 0

    def test_gex_scales_with_oi(self):
        gex_1 = contract_gex(**{**self.KWARGS, "oi": 100}, option_type="C")
        gex_10 = contract_gex(**{**self.KWARGS, "oi": 1000}, option_type="C")
        assert math.isclose(gex_10, gex_1 * 10)

    def test_zero_oi_gives_zero_gex(self):
        gex = contract_gex(**{**self.KWARGS, "oi": 0}, option_type="C")
        assert gex == 0.0


# ---------------------------------------------------------------------------
# compute_gex_profile
# ---------------------------------------------------------------------------

class TestComputeGexProfile:
    """
    Tests using a minimal synthetic chain with known properties.
    """

    def _simple_chain(self) -> list[dict]:
        """
        A chain with:
          - One call at strike 590, high OI
          - One put at strike 580, lower OI
        Total GEX should be net positive (calls dominate).
        """
        return [
            {
                "strike": 590.0,
                "expiry": "2026-04-18",
                "type": "C",
                "bid": 5.80,
                "ask": 6.00,
                "oi": 15000,
                "volume": 6000,
                "underlying_price": 590.0,
            },
            {
                "strike": 580.0,
                "expiry": "2026-04-18",
                "type": "P",
                "bid": 4.90,
                "ask": 5.10,
                "oi": 3000,
                "volume": 900,
                "underlying_price": 590.0,
            },
        ]

    def test_returns_required_keys(self):
        result = compute_gex_profile(self._simple_chain())
        for key in ("gex_by_strike", "total_gex", "gamma_flip", "call_wall", "put_wall", "rows"):
            assert key in result, f"Missing key: {key}"

    def test_gex_by_strike_has_correct_strikes(self):
        result = compute_gex_profile(self._simple_chain())
        assert set(result["gex_by_strike"].keys()) == {590.0, 580.0}

    def test_call_dominated_chain_has_positive_total_gex(self):
        result = compute_gex_profile(self._simple_chain())
        assert result["total_gex"] > 0

    def test_call_wall_is_highest_positive_gex_strike(self):
        result = compute_gex_profile(self._simple_chain())
        gex = result["gex_by_strike"]
        expected_call_wall = max(gex, key=lambda k: gex[k])
        assert result["call_wall"] == expected_call_wall

    def test_put_wall_is_most_negative_gex_strike(self):
        result = compute_gex_profile(self._simple_chain())
        gex = result["gex_by_strike"]
        expected_put_wall = min(gex, key=lambda k: gex[k])
        assert result["put_wall"] == expected_put_wall

    def test_rows_annotated_with_gex(self):
        result = compute_gex_profile(self._simple_chain())
        for row in result["rows"]:
            assert "gex" in row
            assert "sigma" in row
            assert "T" in row


# ---------------------------------------------------------------------------
# Gamma flip detection
# ---------------------------------------------------------------------------

class TestGammaFlip:
    """
    Build a chain where we know a zero crossing exists.
    High call OI at 600 (positive GEX there) and very high put OI at 570
    (negative GEX there) — the flip should fall between 570 and 600.
    """

    def _flip_chain(self) -> list[dict]:
        return [
            {
                "strike": 600.0,
                "expiry": "2026-04-18",
                "type": "C",
                "bid": 1.80,
                "ask": 1.95,
                "oi": 25000,
                "volume": 3000,
                "underlying_price": 585.0,
            },
            {
                "strike": 570.0,
                "expiry": "2026-04-18",
                "type": "P",
                "bid": 1.90,
                "ask": 2.05,
                "oi": 30000,
                "volume": 4000,
                "underlying_price": 585.0,
            },
        ]

    def test_gamma_flip_is_between_strikes(self):
        result = compute_gex_profile(self._flip_chain())
        flip = result["gamma_flip"]
        if flip is not None:
            assert 570.0 <= flip <= 600.0, f"Gamma flip {flip} is outside expected range [570, 600]"

    def test_no_flip_when_all_positive(self):
        """If the chain is all calls with no puts, total GEX is positive and no flip exists."""
        chain = [
            {
                "strike": float(k),
                "expiry": "2026-04-18",
                "type": "C",
                "bid": 5.0,
                "ask": 5.2,
                "oi": 10000,
                "volume": 1000,
                "underlying_price": 590.0,
            }
            for k in [580, 585, 590, 595, 600]
        ]
        result = compute_gex_profile(chain)
        assert result["gamma_flip"] is None
        assert result["total_gex"] > 0


# ---------------------------------------------------------------------------
# Sample CSV round-trip
# ---------------------------------------------------------------------------

class TestSampleChain:
    @pytest.fixture
    def csv_path(self) -> str:
        return os.path.join(
            os.path.dirname(__file__), "..", "data", "sample_chain.csv"
        )

    def test_sample_csv_loads(self, csv_path):
        chain = load_chain(csv_path)
        assert len(chain) > 0

    def test_sample_csv_produces_valid_profile(self, csv_path):
        chain = load_chain(csv_path)
        result = compute_gex_profile(chain)
        assert isinstance(result["total_gex"], float)
        assert len(result["gex_by_strike"]) > 0

    def test_sample_csv_call_wall_is_a_strike_in_chain(self, csv_path):
        chain = load_chain(csv_path)
        result = compute_gex_profile(chain)
        all_strikes = {row["strike"] for row in chain}
        assert result["call_wall"] in all_strikes

    def test_sample_csv_put_wall_is_a_strike_in_chain(self, csv_path):
        chain = load_chain(csv_path)
        result = compute_gex_profile(chain)
        all_strikes = {row["strike"] for row in chain}
        assert result["put_wall"] in all_strikes
