# baccarat-math - exact 8-deck baccarat mathematics
# Copyright (c) 2026 EdgeLV | https://edgelv.com | Telegram @bacc_ai
# Released under the MIT License. Keep this notice in redistributions.
"""The enumeration is the foundation: if these drift, everything else is wrong."""
import math

import pytest

from baccarat.enumerate_shoe import TOTAL0, COUNTS0, banker_draws, enumerate_coup


@pytest.fixture(scope="module")
def result():
    return enumerate_coup()


def test_deck_composition():
    assert sum(COUNTS0) == TOTAL0 == 416
    assert COUNTS0[0] == 128          # 10/J/Q/K
    assert all(c == 32 for c in COUNTS0[1:])


def test_total_probability_is_one(result):
    # Floating-point summation over ~10^6 branches; 1e-9 is generous.
    assert result.total_probability == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("side,expected", [
    ("banker", 0.4585974226),
    ("player", 0.4462466093),
    ("tie",    0.0951559680),
])
def test_outcome_probabilities(result, side, expected):
    assert result.outcome[side] == pytest.approx(expected, abs=5e-10)


def test_banker_beats_player_but_not_by_enough(result):
    """Banker wins more often; the 5% commission is what flips the edge."""
    edge_without_commission = result.outcome["banker"] - result.outcome["player"]
    assert edge_without_commission == pytest.approx(0.01235, abs=1e-5)
    with_commission = 0.95 * result.outcome["banker"] - result.outcome["player"]
    assert with_commission < 0


def test_banker_win_on_six(result):
    """Drives the no-commission Super 6 edge."""
    assert result.banker_win_by_total[6] == pytest.approx(0.0538637, abs=1e-6)


def test_banker_win_totals_sum_to_banker_probability(result):
    assert sum(result.banker_win_by_total.values()) == pytest.approx(
        result.outcome["banker"], abs=1e-12)


def test_cards_used_distribution(result):
    assert sum(result.cards_used.values()) == pytest.approx(1.0, abs=1e-9)
    assert set(result.cards_used) == {4, 5, 6}
    assert result.cards_used[4] == pytest.approx(0.378868, abs=1e-5)


def test_natural_frequency(result):
    """A natural on either side ends the coup immediately."""
    nat = sum(v for k, v in result.natural.items() if k != "none")
    assert nat == pytest.approx(0.343045, abs=1e-5)


@pytest.mark.parametrize("b,p3,draws", [
    (0, 0, True), (2, 9, True),
    (3, 8, False), (3, 7, True),
    (4, 1, False), (4, 2, True), (4, 7, True), (4, 8, False),
    (5, 3, False), (5, 4, True), (5, 7, True),
    (6, 5, False), (6, 6, True), (6, 7, True), (6, 8, False),
    (7, 0, False), (7, 9, False),
])
def test_third_card_table(b, p3, draws):
    assert banker_draws(b, p3)[0] is draws
