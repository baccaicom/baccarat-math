# baccarat-math - exact 8-deck baccarat mathematics
# Copyright (c) 2026 EdgeLV | https://edgelv.com | Telegram @bacc_ai
# Released under the MIT License. Keep this notice in redistributions.
"""
Risk of ruin for flat betting, computed exactly.

Why not the textbook gambler's-ruin formula: it assumes every result is
+/-1 unit. A winning banker bet pays 0.95 and a tie returns the stake, so
the payouts are asymmetric and the closed form gives the wrong answer.

Instead this propagates the full distribution of the bankroll hand by hand
on a lattice of 1/20 of a unit (0.95 and 1.00 are both exact multiples of
1/20, so nothing is rounded). No sampling, so no error term.

Ruin is defined as "cannot cover another bet", not "balance reached zero":
with 200 left and a 500 unit you are already done.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .enumerate_shoe import enumerate_coup

__all__ = ["RuinResult", "risk_of_ruin", "GRID"]

GRID = 20          # lattice steps per unit
_WIN = 19          # +0.95 units
_LOSE = -20        # -1.00 units


@dataclass(frozen=True)
class RuinResult:
    units: int
    hands: int
    ruin: float            # P(cannot cover a bet at some point)
    finished_ahead: float  # P(end above the starting bankroll)
    side: str

    def __str__(self) -> str:
        return (f"{self.units:>4} units / {self.hands:>5} hands  "
                f"ruin {self.ruin * 100:6.2f}%   ahead {self.finished_ahead * 100:6.2f}%")


def risk_of_ruin(units: int, hands: int, side: str = "banker",
                 cap_units: int = 400) -> RuinResult:
    """Flat-bet `units` bankroll for `hands` hands. Exact.

    `cap_units` bounds the lattice; probability mass above it is pinned
    there, which only ever understates how far ahead a run finished and
    never affects the ruin figure.
    """
    r = enumerate_coup()
    p_win = r.outcome["banker" if side == "banker" else "player"]
    p_lose = r.outcome["player" if side == "banker" else "banker"]
    p_push = r.outcome["tie"]
    win_step = _WIN if side == "banker" else GRID   # player pays even money

    n = cap_units * GRID + 1
    start = units * GRID
    v = np.zeros(n)
    v[start] = 1.0
    ruined = 0.0

    for _ in range(hands):
        low = v[:GRID].sum()        # below one unit -> cannot bet again
        ruined += low
        v[:GRID] = 0.0
        idx = np.nonzero(v)[0]
        if idx.size == 0:
            break
        nxt = np.zeros(n)
        np.add.at(nxt, np.minimum(idx + win_step, n - 1), v[idx] * p_win)
        np.add.at(nxt, idx + _LOSE, v[idx] * p_lose)
        np.add.at(nxt, idx, v[idx] * p_push)
        v = nxt

    ruined += v[:GRID].sum()
    v[:GRID] = 0.0
    return RuinResult(units, hands, ruined, float(v[start + 1:].sum()), side)


if __name__ == "__main__":  # pragma: no cover
    hands_grid = (100, 300, 500, 1000)
    print("Flat-betting banker. Probability of busting before you walk away.\n")
    print(f"{'bankroll':<12}" + "".join(f"{h:>10} hands" for h in hands_grid))
    print("-" * 76)
    for u in (10, 20, 40, 100):
        row = [f"{risk_of_ruin(u, h).ruin * 100:>15.1f}%" for h in hands_grid]
        print(f"{str(u) + ' units':<12}" + "".join(row))
    print("\nStill-ahead probability at 100 units (ruin is ~0 throughout):")
    for h in hands_grid:
        res = risk_of_ruin(100, h)
        print(f"  {h:>5} hands: {res.finished_ahead * 100:.1f}%")
    print("\nA shoe gives ~74 decided hands, so 500 hands is about seven shoes.")

    from . import print_source_notice
    print_source_notice()
