# baccarat-math - exact 8-deck baccarat mathematics
# Copyright (c) 2026 EdgeLV | https://edgelv.com | Telegram @bacc_ai
# Released under the MIT License. Keep this notice in redistributions.
import math

import pytest

from baccarat.enumerate_shoe import enumerate_coup
from baccarat.pattern_test import comparison_table, sweep
from baccarat.shoe import deal_shoe, outcome_stream
import random


def test_comparison_table_analytics():
    rows = {r.length: r for r in comparison_table(range(2, 9))}
    assert rows[6].candidates == 64
    assert rows[6].expected_significant == pytest.approx(3.2)
    assert rows[6].p_at_least_one == pytest.approx(1 - 0.95 ** 64, abs=1e-12)
    assert rows[6].p_at_least_one == pytest.approx(0.96248, abs=1e-5)
    assert rows[6].bonferroni == pytest.approx(0.05 / 64)


def test_shoe_matches_exact_probabilities():
    """The dealer must reproduce the enumeration, or the sweep is meaningless."""
    seq = list(outcome_stream(3000, seed=1, drop_ties=False))
    n = len(seq)
    exact = enumerate_coup().outcome
    for code, name in (("B", "banker"), ("P", "player"), ("T", "tie")):
        obs = seq.count(code) / n
        th = exact[name]
        sigma = math.sqrt(th * (1 - th) / n)
        assert abs(obs - th) < 4 * sigma, f"{name}: {obs:.5f} vs {th:.5f}"


def test_ties_are_dropped_by_default():
    assert "T" not in set(outcome_stream(20, seed=2))


def test_shoe_length_is_plausible():
    rng = random.Random(3)
    lengths = [len(deal_shoe(rng)) for _ in range(200)]
    assert 70 < sum(lengths) / len(lengths) < 90


def test_bonferroni_kills_the_false_positives():
    """
    In random data a length-6 sweep usually turns up something at p<0.05.
    None of it should survive correction. This is the whole argument.
    """
    res = sweep(6, shoes=1500, seed=5)
    assert len(res["significant_corrected"]) == 0
