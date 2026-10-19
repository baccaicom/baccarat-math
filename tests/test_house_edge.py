# baccarat-math - exact 8-deck baccarat mathematics
# Copyright (c) 2026 EdgeLV | https://edgelv.com | Telegram @bacc_ai
# Released under the MIT License. Keep this notice in redistributions.
import pytest

from baccarat.house_edge import PAIR_PROB, all_bets, hourly_cost

EXPECTED = {
    "Banker (5% commission)":          0.010579,
    "Player":                          0.012351,
    "Banker (no-commission Super 6)":  0.014581,
    "Tie":                             0.143596,
    "Tie (9:1 rule)":                  0.048440,
    "Pair (either side)":              0.103614,
}


@pytest.fixture(scope="module")
def bets():
    return {b.name: b for b in all_bets()}


@pytest.mark.parametrize("name,edge", EXPECTED.items())
def test_house_edge(bets, name, edge):
    assert bets[name].house_edge == pytest.approx(edge, abs=1e-5)


def test_every_main_bet_is_negative_ev(bets):
    assert all(b.ev < 0 for b in bets.values())


def test_no_commission_is_worse_than_commission(bets):
    """The selling point of Super 6 is removing the rake. It still costs more."""
    assert (bets["Banker (no-commission Super 6)"].house_edge
            > bets["Banker (5% commission)"].house_edge)


def test_pair_probability():
    assert PAIR_PROB == pytest.approx(31 / 415)


def test_hourly_cost(bets):
    assert hourly_cost(bets["Banker (5% commission)"], 100, 70) == pytest.approx(74.0, abs=0.5)
