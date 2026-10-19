# baccarat-math

Exact probabilities for 8-deck baccarat, plus the three things people
usually get wrong about them: risk of ruin, staking systems, and
"patterns" in the road.

Everything here is computed, not quoted. The core numbers come from a full
recursion over all 416 cards dealt without replacement — closed form, no
sampling, no error term. Where simulation is genuinely required (staking
systems), the error is reported alongside the estimate.

```
$ python -m baccarat.enumerate_shoe
total probability (should be 1): 0.999999999999

banker 45.8597%   player 44.6247%   tie 9.5156%
```

## The results

### House edge, per hand wagered

| Bet | Payout | Hit rate | House edge | Cost/hour at 100 × 70 hands |
|---|---|---|---|---|
| Banker (5% commission) | 0.95 : 1 | 45.86% | **1.058%** | 74 |
| Player | 1 : 1 | 44.62% | **1.235%** | 86 |
| Banker (no-commission Super 6) | 1 : 1 | 45.86% | **1.458%** | 102 |
| Tie | 8 : 1 | 9.52% | **14.360%** | 1,005 |
| Tie (9:1 rule) | 9 : 1 | 9.52% | **4.844%** | 339 |
| Pair (either side) | 11 : 1 | 7.47% | **10.361%** | 725 |

The Super 6 row is the interesting one. Removing the 5% commission sounds
like a discount; paying half on a banker win with a total of 6 is the
price. That happens on **5.3864%** of hands, which costs more than the
commission it saves — the edge goes *up*, from 1.058% to 1.458%.

### Risk of ruin, flat betting banker

Exact, not simulated. Ruin means "cannot cover another bet", not "balance
reached zero".

| Bankroll | 100 hands | 300 hands | 500 hands | 1,000 hands |
|---|---|---|---|---|
| 10 units | 34.5% | 62.0% | 72.1% | 82.7% |
| 20 units | 4.4% | 28.4% | 43.5% | 62.7% |
| 40 units | 0.0% | 2.2% | 9.1% | 27.8% |
| 100 units | 0.0% | 0.0% | 0.0% | 0.2% |

A bankroll is a ratio, not an amount: 10,000 at 500 a hand and 1,000 at 50
a hand are the same 20 units and carry the same risk.

Note what 100 units buys. Ruin is ~0 — and only **40.1%** of those
sessions finish above where they started. A deep bankroll does not buy a
profit; it buys the right to lose slowly.

### Staking systems

20-unit bankroll, 100 per unit, target +5 units, 200-hand cap,
100,000 sessions each.

| Progression | Hit target | Busted | Avg hands | Avg wagered | **Loss ÷ wagered** |
|---|---|---|---|---|---|
| Flat | 63.2% | 14.9% | 97.6 | 9,765 | **1.066% ± 0.029** |
| Martingale | 77.2% | 22.8% | 14.7 | 3,272 | **1.098% ± 0.103** |
| D'Alembert | 76.0% | 24.0% | 14.5 | 3,835 | **1.144% ± 0.092** |
| 1-3-2-4 | 73.2% | 26.5% | 32.9 | 6,085 | **1.067% ± 0.055** |

Theoretical banker house edge: **1.058%**. Every progression lands on it
within one bootstrap sigma.

Martingale really does hit the target more often — 77% against flat
betting's 63%. It also busts more often, and its average result is
negative. It appears to "lose less" only because it ends sessions after
14.7 hands instead of 97.6, so less money goes through the table. Per unit
wagered the four are identical. A progression redistributes the shape of
winning and losing; it cannot change the total.

### "Patterns" in the road

`p < 0.05` means that if a pattern has no predictive power, chance alone
still makes it look this striking 5% of the time. Test one pattern and
that threshold is reasonable. Nobody tests one.

| Pattern length | Candidates | Expected "significant" | P(at least one) | Bonferroni threshold |
|---|---|---|---|---|
| 3 | 8 | 0.40 | 33.7% | 0.00625 |
| 4 | 16 | 0.80 | 56.0% | 0.00313 |
| 5 | 32 | 1.60 | 80.6% | 0.00156 |
| 6 | 64 | 3.20 | 96.2% | 0.00078 |
| 7 | 128 | 6.40 | 99.9% | 0.00039 |
| 8 | 256 | 12.80 | >99.99% | 0.00020 |

`pattern_test` also does it empirically, on shoes it deals itself:

```
Empirical check, length 6, 3000 shoes:
  219,201 decided hands, banker rate 50.44%
  patterns with p < 0.05 uncorrected : 1
  surviving Bonferroni (p < 0.00078)  : 0
    PPPBBB  n=3471   next-banker 52.75%  p=0.0065
```

`PPPBBB` occurs 3,471 times and is followed by banker 52.75% of the time
against a 50.44% baseline, at p = 0.0065. That is exactly the kind of
finding somebody builds a system on. There is no structure in this data —
the shoes were dealt by a PRNG — and the correction removes it.

## Running it

Python 3.10+. Only `numpy` is required, and only for the two modules that
need fast array work.

```bash
pip install -r requirements.txt

python -m baccarat.enumerate_shoe    # exact probabilities, < 1s
python -m baccarat.house_edge        # EV of every bet
python -m baccarat.risk_of_ruin      # exact DP, ~7s
python -m baccarat.staking           # 400k simulated sessions, ~30s
python -m baccarat.pattern_test      # multiple-comparison demo
```

Tests:

```bash
pip install pytest && pytest -q        # 70 tests, ~25s
```

The test suite pins the published figures, checks the shoe dealer against
the exact enumeration to within 4 sigma, and asserts the claim the staking
module exists to make — that every progression converges to the house edge
per unit wagered.

## How it works

**`enumerate_shoe`** recurses over the multiset of remaining ranks rather
than individual cards. At most four cards are drawn after the initial
four, and there are only ten distinct ranks to branch on at each step,
which keeps the whole thing well under a second. All outcome probabilities
sum to 0.999999999999; the remainder is floating-point rounding.

**`risk_of_ruin`** does not use the textbook gambler's-ruin formula, which
assumes every result is ±1 unit. A winning banker bet pays 0.95 and a tie
returns the stake, so the payouts are asymmetric and the closed form gives
the wrong answer. Instead it propagates the full bankroll distribution
hand by hand on a lattice of 1/20 of a unit — both 0.95 and 1.00 are exact
multiples, so nothing is rounded.

**`staking`** settles each hand on the exact probabilities. When the
bankroll cannot cover the full bet, the remaining balance goes in. Error
bars are bootstrap, 400 resamples.

**`shoe`** deals real 8-deck shoes under the full drawing rules, with a
cut card. Verified against the enumeration: over 646,377 hands the three
outcomes land within 0.26σ, 0.37σ and 1.07σ of their exact values.

## Interactive versions

Each of these runs in the browser, with your own inputs, at
[edgelv.com](https://edgelv.com/en/tools/):

- [Expected-value calculator](https://edgelv.com/en/tools/house-edge/)
- [Risk-of-ruin calculator](https://edgelv.com/en/tools/risk-of-ruin/)
- [Betting-system simulator](https://edgelv.com/en/tools/betting-systems/)
- [Pattern tester](https://edgelv.com/en/tools/pattern-test/)

## A note on what this is for

Every main bet in baccarat has negative expectation. Nothing in this
repository is a betting strategy, and the four modules exist to verify the
same fact from four angles. If a number here disagrees with something you
have read elsewhere, the code is right here — check it.

## License

MIT. See [LICENSE](LICENSE).
