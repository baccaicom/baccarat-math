"""
Staking systems (Martingale, D'Alembert, 1-3-2-4, flat) by Monte Carlo.

The point of this module is one column: loss divided by total amount
wagered. Whatever the progression does to the *shape* of winning and
losing, that ratio converges to the house edge of the underlying bet,
because a progression only chooses how much goes on each hand and how
many hands there are. It cannot change the expectation of a single unit.

Each hand settles on the exact probabilities from `enumerate_shoe`.
When the bankroll cannot cover the full bet, the remaining balance goes in.
A session ends on reaching the target, on busting, or at the hand cap.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .enumerate_shoe import enumerate_coup

__all__ = ["SYSTEMS", "SessionStats", "simulate", "bootstrap_se"]

SYSTEMS = ("flat", "martingale", "dalembert", "1-3-2-4")
_SEQ_1324 = (1, 3, 2, 4)


@dataclass(frozen=True)
class SessionStats:
    system: str
    hit_target: float     # share of sessions that reached the goal
    busted: float
    mean_net: float
    mean_hands: float
    mean_wagered: float
    loss_per_wagered: float   # the column that matters

    def __str__(self) -> str:
        return (f"{self.system:<12}{self.hit_target * 100:>8.1f}%"
                f"{self.busted * 100:>8.1f}%{self.mean_hands:>11.1f}"
                f"{self.mean_wagered:>14,.0f}{self.loss_per_wagered * 100:>13.3f}%")


def _next_bet(system: str, unit: float, step: float, k: int) -> float:
    if system == "flat":
        return unit
    if system in ("martingale", "dalembert"):
        return unit * step
    return unit * _SEQ_1324[k]


def _advance(system: str, won: bool, step: float, k: int) -> tuple[float, int]:
    if system == "martingale":
        return (1.0 if won else step * 2), k
    if system == "dalembert":
        return (max(1.0, step - 1) if won else step + 1), k
    if system == "1-3-2-4":
        return step, ((k + 1) % 4 if won else 0)
    return step, k


def _run(system: str, bank_units: int, unit: float, goal_units: int,
         max_hands: int, n: int, seed: int) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Returns (net per session, wagered per session, goals hit, busts)."""
    r = enumerate_coup()
    p_b, p_p = r.outcome["banker"], r.outcome["player"]

    rng = np.random.default_rng(seed)
    bank = bank_units * unit
    goal = bank + goal_units * unit
    nets = np.empty(n)
    wagered = np.empty(n)
    hands = np.empty(n)
    goals = busts = 0

    for i in range(n):
        bal, step, k, h, w = bank, 1.0, 0, 0, 0.0
        for _ in range(max_hands):
            bet = min(_next_bet(system, unit, step, k), bal)
            if bet < 1e-9:
                break
            draw = rng.random()
            h += 1
            w += bet
            if draw < p_b:
                bal += 0.95 * bet       # banker, commission already taken
                won: bool | None = True
            elif draw < p_b + p_p:
                bal -= bet
                won = False
            else:
                won = None              # tie: stake returned
            if won is not None:
                step, k = _advance(system, won, step, k)
            if bal >= goal:
                goals += 1
                break
            if bal < unit:
                busts += 1
                break
        nets[i], wagered[i], hands[i] = bal - bank, w, h
    return nets, wagered, goals, busts, hands


def simulate(system: str, bank_units: int = 20, unit: float = 100,
             goal_units: int = 5, max_hands: int = 200,
             n: int = 100_000, seed: int = 7) -> SessionStats:
    nets, wagered, goals, busts, hands = _run(
        system, bank_units, unit, goal_units, max_hands, n, seed)
    return SessionStats(
        system=system,
        hit_target=goals / n,
        busted=busts / n,
        mean_net=float(nets.mean()),
        mean_hands=float(hands.mean()),
        mean_wagered=float(wagered.mean()),
        loss_per_wagered=float(-nets.mean() / wagered.mean()),
    )


def bootstrap_se(system: str, resamples: int = 400, seed: int = 7,
                 boot_seed: int = 1, **kw) -> tuple[float, float]:
    """Bootstrap mean and 1-sigma of loss/wagered."""
    n = kw.pop("n", 100_000)
    nets, wagered, *_ = _run(system, kw.pop("bank_units", 20), kw.pop("unit", 100),
                             kw.pop("goal_units", 5), kw.pop("max_hands", 200), n, seed)
    b = np.random.default_rng(boot_seed)
    ratios = np.empty(resamples)
    for j in range(resamples):
        idx = b.integers(0, n, n)
        ratios[j] = -nets[idx].mean() / wagered[idx].mean()
    return float(ratios.mean()), float(ratios.std())


if __name__ == "__main__":  # pragma: no cover
    from .house_edge import all_bets
    edge = all_bets()[0].house_edge
    print("Bankroll 20 units, unit 100, target +5 units, 200-hand cap, "
          "100,000 sessions each.\n")
    print(f"{'system':<12}{'target':>8}{'busted':>8}{'avg hands':>11}"
          f"{'avg wagered':>14}{'loss/wagered':>14}")
    print("-" * 67)
    for s in SYSTEMS:
        print(simulate(s))
    print(f"\nTheoretical banker house edge: {edge * 100:.3f}%")
    print("Bootstrap 1-sigma on loss/wagered:")
    for s in SYSTEMS:
        m, sd = bootstrap_se(s)
        print(f"  {s:<12}{m * 100:6.3f}% +/- {sd * 100:.3f}")
