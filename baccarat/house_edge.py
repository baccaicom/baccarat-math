# baccarat-math - exact 8-deck baccarat mathematics
# Copyright (c) 2026 EdgeLV | https://edgelv.com | Telegram @bacc_ai
# Released under the MIT License. Keep this notice in redistributions.
"""
Expected value of every baccarat bet, from the exact enumeration.

House edge here is quoted *per hand wagered*, including ties (on which the
main bets push). Quoting per *decided* hand instead raises the numbers by a
factor of 1/(1 - P(tie)); both are given.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enumerate_shoe import enumerate_coup

__all__ = ["Bet", "all_bets", "PAIR_PROB", "hourly_cost"]

# Either side's first two cards being the same rank, 8 decks:
# 31 matching cards left among the 415 that remain after the first.
PAIR_PROB: float = 31 / 415


@dataclass(frozen=True)
class Bet:
    name: str
    payout: str
    hit_rate: float          # P(the bet wins)
    ev: float                # expected value per unit staked, per hand
    note: str = ""

    @property
    def house_edge(self) -> float:
        return -self.ev


def all_bets() -> list[Bet]:
    r = enumerate_coup()
    pb = r.outcome["banker"]
    pp = r.outcome["player"]
    pt = r.outcome["tie"]
    pb6 = r.banker_win_by_total[6]

    return [
        Bet("Banker (5% commission)", "0.95 : 1", pb, 0.95 * pb - pp),
        Bet("Player", "1 : 1", pp, 1.00 * pp - pb),
        Bet(
            "Banker (no-commission Super 6)", "1 : 1 *", pb,
            (pb - pb6) + 0.5 * pb6 - pp,
            note=("no rake, but a banker win on 6 pays half. "
                  f"That happens on {pb6 * 100:.4f}% of hands, which costs "
                  "more than the commission it saves."),
        ),
        Bet("Tie", "8 : 1", pt, 8 * pt - (1 - pt)),
        Bet("Tie (9:1 rule)", "9 : 1", pt, 9 * pt - (1 - pt)),
        Bet("Pair (either side)", "11 : 1", PAIR_PROB,
            11 * PAIR_PROB - (1 - PAIR_PROB)),
    ]


def hourly_cost(bet: Bet, stake: float, hands_per_hour: int) -> float:
    """Expected loss over an hour at this stake and pace."""
    return bet.house_edge * stake * hands_per_hour


if __name__ == "__main__":  # pragma: no cover
    r = enumerate_coup()
    pt = r.outcome["tie"]
    bets = all_bets()
    print(f"{'bet':<32}{'payout':>10}{'hit':>9}{'edge':>9}"
          f"{'edge/decided':>14}{'100 x 70/h':>12}")
    print("-" * 86)
    for b in bets:
        per_decided = b.house_edge / (1 - pt) if b.name.startswith(("Banker", "Player")) else float("nan")
        pd = f"{per_decided * 100:.3f}%" if per_decided == per_decided else "-"
        print(f"{b.name:<32}{b.payout:>10}{b.hit_rate * 100:>8.2f}%"
              f"{b.house_edge * 100:>8.3f}%{pd:>14}"
              f"{hourly_cost(b, 100, 70):>11.0f}")
    print("\n* " + bets[2].note)

    from . import print_source_notice
    print_source_notice()
