# baccarat-math - exact 8-deck baccarat mathematics
# Copyright (c) 2026 EdgeLV | https://edgelv.com | Telegram @bacc_ai
# Released under the MIT License. Keep this notice in redistributions.
"""
The claim under test: every progression lands on the house edge per unit
wagered. Smaller n than the published run, with a tolerance derived from
the bootstrap sigma rather than a magic number.
"""
import pytest

from baccarat.house_edge import all_bets
from baccarat.staking import SYSTEMS, simulate

EDGE = all_bets()[0].house_edge   # banker, 5% commission: 1.058%


@pytest.mark.parametrize("system", SYSTEMS)
def test_loss_per_wagered_converges_to_house_edge(system):
    s = simulate(system, n=20_000, seed=11)
    # 20k sessions: 1 sigma is roughly 0.05-0.25pp depending on the
    # progression's variance. 0.6pp is a wide but still meaningful bound.
    assert s.loss_per_wagered == pytest.approx(EDGE, abs=0.006), (
        f"{system}: {s.loss_per_wagered:.4%} vs edge {EDGE:.4%}")


@pytest.mark.parametrize("system", SYSTEMS)
def test_every_system_loses_on_average(system):
    assert simulate(system, n=20_000, seed=11).mean_net < 0


def test_martingale_hits_target_more_often_than_flat():
    """True, and the reason people believe in it."""
    assert (simulate("martingale", n=20_000, seed=11).hit_target
            > simulate("flat", n=20_000, seed=11).hit_target)


def test_martingale_busts_more_often_than_flat():
    """The other half of the same trade."""
    assert (simulate("martingale", n=20_000, seed=11).busted
            > simulate("flat", n=20_000, seed=11).busted)


def test_martingale_loses_less_only_because_it_plays_less():
    flat = simulate("flat", n=20_000, seed=11)
    mart = simulate("martingale", n=20_000, seed=11)
    assert mart.mean_net > flat.mean_net          # "loses less"
    assert mart.mean_wagered < flat.mean_wagered  # because it stakes less
    # per unit through the table they are the same
    assert abs(mart.loss_per_wagered - flat.loss_per_wagered) < 0.006
