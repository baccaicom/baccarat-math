"""
What scanning for "patterns" in the road actually finds.

p < 0.05 means: if a pattern has no predictive power, chance alone still
makes it look this striking 5% of the time. Test one pattern and that
threshold is reasonable. Nobody tests one. Sweep every pattern of length
k and there are 2^k of them, so you should *expect* 0.05 x 2^k of them to
come back "significant" in data that is purely random.

This module gives both halves: the analytic expectation, and an empirical
sweep over real dealt shoes so you can watch it happen.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from itertools import product

from .shoe import outcome_stream

__all__ = ["MultipleComparison", "comparison_table", "sweep"]


@dataclass(frozen=True)
class MultipleComparison:
    length: int
    candidates: int
    expected_significant: float
    p_at_least_one: float
    bonferroni: float


def comparison_table(lengths: range | tuple[int, ...] = range(2, 9),
                     alpha: float = 0.05) -> list[MultipleComparison]:
    rows = []
    for k in lengths:
        m = 2 ** k
        rows.append(MultipleComparison(
            length=k,
            candidates=m,
            expected_significant=alpha * m,
            p_at_least_one=1 - (1 - alpha) ** m,
            bonferroni=alpha / m,
        ))
    return rows


def _two_sided_p(successes: int, trials: int, p0: float) -> float:
    """Normal-approximation two-sided p-value for a single proportion."""
    if trials == 0:
        return 1.0
    se = math.sqrt(p0 * (1 - p0) / trials)
    if se == 0:
        return 1.0
    z = (successes / trials - p0) / se
    return math.erfc(abs(z) / math.sqrt(2))


@dataclass(frozen=True)
class Finding:
    pattern: str
    occurrences: int
    next_banker: int
    rate: float
    p_raw: float


def sweep(length: int, shoes: int = 2000, seed: int = 0,
          alpha: float = 0.05, min_occurrences: int = 100) -> dict:
    """Scan every pattern of `length` over freshly dealt shoes.

    Returns the findings that clear `alpha` uncorrected, and how many of
    those survive Bonferroni. In random data the second number should
    almost always be zero while the first is not.
    """
    seq = list(outcome_stream(shoes, seed=seed))
    p0 = seq.count("B") / len(seq)         # empirical banker rate among decided hands

    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for i in range(len(seq) - length):
        key = "".join(seq[i:i + length])
        counts[key][0] += 1
        if seq[i + length] == "B":
            counts[key][1] += 1

    findings = []
    for pat in map("".join, product("BP", repeat=length)):
        occ, nb = counts.get(pat, [0, 0])
        if occ < min_occurrences:
            continue
        findings.append(Finding(pat, occ, nb, nb / occ, _two_sided_p(nb, occ, p0)))

    m = 2 ** length
    raw = [f for f in findings if f.p_raw < alpha]
    corrected = [f for f in findings if f.p_raw < alpha / m]
    return {
        "hands": len(seq),
        "banker_rate": p0,
        "patterns_tested": len(findings),
        "significant_raw": sorted(raw, key=lambda f: f.p_raw),
        "significant_corrected": corrected,
        "bonferroni": alpha / m,
    }


if __name__ == "__main__":  # pragma: no cover
    print("Sweeping every pattern of a given length through random shoes.\n")
    print(f"{'length':>7}{'candidates':>13}{'expected sig.':>16}"
          f"{'P(>=1)':>10}{'Bonferroni':>13}")
    print("-" * 59)
    for row in comparison_table(range(3, 9)):
        pa = ">99.99%" if row.p_at_least_one > 0.9999 else f"{row.p_at_least_one * 100:.1f}%"
        print(f"{row.length:>7}{row.candidates:>13}"
              f"{row.expected_significant:>16.2f}{pa:>10}{row.bonferroni:>13.5f}")

    # Length 6: 64 candidates, so ~3.2 false positives are expected and
    # P(at least one) is 96%. That makes the point far better than length 4,
    # where 44% of the time you happen to find nothing.
    print("\nEmpirical check, length 6, 3000 shoes:")
    res = sweep(6, shoes=3000)
    print(f"  {res['hands']:,} decided hands, banker rate {res['banker_rate'] * 100:.2f}%")
    print(f"  patterns with p < 0.05 uncorrected : {len(res['significant_raw'])}")
    print(f"  surviving Bonferroni (p < {res['bonferroni']:.5f})  : "
          f"{len(res['significant_corrected'])}")
    for f in res["significant_raw"][:5]:
        print(f"    {f.pattern}  n={f.occurrences:<6} next-banker {f.rate * 100:5.2f}%  "
              f"p={f.p_raw:.4f}")
    print("\n  There is no predictable structure in this data. Every hit above"
          "\n  is a false positive, which is exactly the point.")
