"""
Deal real 8-deck shoes under the full drawing rules.

Used by `pattern_test` to produce outcome sequences to scan. Pure stdlib.
"""
from __future__ import annotations

import random
from typing import Iterator

from .enumerate_shoe import banker_draws

__all__ = ["deal_shoe", "outcome_stream"]

_DECK = ([0] * 16 + [v for v in range(1, 10) for _ in range(4)]) * 8  # 416 cards


def deal_shoe(rng: random.Random, penetration: int = 14) -> list[str]:
    """Deal one shoe, return outcomes as 'B' / 'P' / 'T' in order.

    `penetration` is how many cards are left behind the cut card.
    """
    cards = _DECK[:]
    rng.shuffle(cards)
    i, n = 0, len(cards) - penetration
    out: list[str] = []

    while i + 6 <= n:                     # room for the longest coup
        p = (cards[i] + cards[i + 2]) % 10
        b = (cards[i + 1] + cards[i + 3]) % 10
        i += 4
        if p not in (8, 9) and b not in (8, 9):
            if p <= 5:
                p3 = cards[i]
                i += 1
                p = (p + p3) % 10
                if banker_draws(b, p3)[0]:
                    b = (b + cards[i]) % 10
                    i += 1
            elif b <= 5:
                b = (b + cards[i]) % 10
                i += 1
        out.append("B" if b > p else "P" if p > b else "T")
    return out


def outcome_stream(shoes: int, seed: int = 0, drop_ties: bool = True) -> Iterator[str]:
    """Yield outcomes across `shoes` shoes.

    Ties are dropped by default because that is how the big road records
    them: a tie is drawn as a slash and does not break the B/P sequence.
    """
    rng = random.Random(seed)
    for _ in range(shoes):
        for o in deal_shoe(rng):
            if drop_ties and o == "T":
                continue
            yield o
