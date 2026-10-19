"""
Exact enumeration of an 8-deck baccarat coup.

Every one of the 416 cards is dealt without replacement through a full
recursion over the drawing rules, so the results below are closed-form
probabilities, not sampled estimates. There is no error term.

Card values: 0 = 10/J/Q/K (16 per deck x 8 = 128 cards), 1..9 = 4 per deck
x 8 = 32 cards each. Total 416.

The recursion is over the *multiset* of remaining ranks rather than over
individual cards, which is what keeps it tractable: at most four cards are
drawn, and at each step there are only ten distinct ranks to branch on.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterator

__all__ = [
    "COUNTS0", "TOTAL0", "banker_draws", "enumerate_coup", "Result",
]

COUNTS0: tuple[int, ...] = (128,) + (32,) * 9
TOTAL0: int = 416


def banker_draws(banker_total: int, player_third: int) -> tuple[bool, str]:
    """Banker's drawing decision when the player drew `player_third`.

    Returns (draws, rule_label). This is the standard "third card table";
    the labels are what the frequency report keys on.
    """
    if banker_total <= 2:
        return True, "B0-2 always draws"
    if banker_total == 3:
        return player_third != 8, "B3 draws unless player's third is 8"
    if banker_total == 4:
        return 2 <= player_third <= 7, "B4 draws on player's 2-7"
    if banker_total == 5:
        return 4 <= player_third <= 7, "B5 draws on player's 4-7"
    if banker_total == 6:
        return 6 <= player_third <= 7, "B6 draws on player's 6-7"
    return False, "B7 stands"


def _draw(counts: tuple[int, ...], left: int) -> Iterator[tuple[int, float, tuple[int, ...], int]]:
    """Yield (rank, probability of drawing it, remaining counts, remaining total)."""
    for rank in range(10):
        n = counts[rank]
        if not n:
            continue
        nxt = list(counts)
        nxt[rank] = n - 1
        yield rank, n / left, tuple(nxt), left - 1


class Result:
    """Accumulated probabilities over the full enumeration."""

    def __init__(self) -> None:
        self.outcome: dict[str, float] = defaultdict(float)
        self.banker_win_by_total: dict[int, float] = defaultdict(float)
        self.cards_used: dict[int, float] = defaultdict(float)
        self.natural: dict[str, float] = defaultdict(float)
        self.player_action: dict[str, float] = defaultdict(float)
        self.rule_fired: dict[str, float] = defaultdict(float)

    @property
    def total_probability(self) -> float:
        return sum(self.outcome.values())

    def _settle(self, p: int, b: int, prob: float) -> None:
        if b > p:
            self.outcome["banker"] += prob
            self.banker_win_by_total[b] += prob
        elif p > b:
            self.outcome["player"] += prob
        else:
            self.outcome["tie"] += prob


def enumerate_coup() -> Result:
    """Run the full recursion. Takes well under a second."""
    res = Result()

    def settle(p: int, b: int, prob: float, cards: int, nat: str,
               action: str, rule: str | None) -> None:
        res.cards_used[cards] += prob
        res.natural[nat] += prob
        res.player_action[action] += prob
        if rule:
            res.rule_fired[rule] += prob
        res._settle(p, b, prob)

    for p1, q1, c1, l1 in _draw(COUNTS0, TOTAL0):
        for b1, q2, c2, l2 in _draw(c1, l1):
            for p2, q3, c3, l3 in _draw(c2, l2):
                for b2, q4, c4, l4 in _draw(c3, l3):
                    base = q1 * q2 * q3 * q4
                    p = (p1 + p2) % 10
                    b = (b1 + b2) % 10

                    p_nat, b_nat = p in (8, 9), b in (8, 9)
                    if p_nat or b_nat:
                        nat = ("both" if p_nat and b_nat
                               else "player" if p_nat else "banker")
                        settle(p, b, base, 4, nat, "natural - both stand", None)
                        continue

                    if p <= 5:
                        for p3, q5, c5, l5 in _draw(c4, l4):
                            pr5 = base * q5
                            p_tot = (p + p3) % 10
                            draws, rule = banker_draws(b, p3)
                            if draws:
                                for b3, q6, _c6, _l6 in _draw(c5, l5):
                                    settle(p_tot, (b + b3) % 10, pr5 * q6, 6,
                                           "none", "player draws", rule)
                            else:
                                settle(p_tot, b, pr5, 5, "none", "player draws", rule)
                    else:
                        if b <= 5:
                            for b3, q5, _c5, _l5 in _draw(c4, l4):
                                settle(p, (b + b3) % 10, base * q5, 5, "none",
                                       "player stands", "B0-5 draws when player stands")
                        else:
                            settle(p, b, base, 4, "none", "player stands",
                                   "B6-7 stands when player stands")
    return res


if __name__ == "__main__":  # pragma: no cover
    r = enumerate_coup()
    pc = lambda x: f"{x * 100:.4f}%"
    print(f"total probability (should be 1): {r.total_probability:.12f}\n")
    print(f"banker {pc(r.outcome['banker'])}   "
          f"player {pc(r.outcome['player'])}   tie {pc(r.outcome['tie'])}\n")
    print("banker wins, by winning total:")
    for k in sorted(r.banker_win_by_total):
        print(f"  {k}: {pc(r.banker_win_by_total[k])}")
    print("\ncards used in the coup:")
    for k in sorted(r.cards_used):
        print(f"  {k}: {pc(r.cards_used[k])}")
    print("\nrule firing frequency:")
    for k, v in sorted(r.rule_fired.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<42} {pc(v)}")
