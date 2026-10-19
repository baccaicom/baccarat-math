import pytest

from baccarat.risk_of_ruin import risk_of_ruin

# Published values (exact DP, so these are not tolerances on noise —
# a change here means the algorithm changed).
PUBLISHED = {
    (10, 100): 0.345, (10, 300): 0.620, (10, 500): 0.721, (10, 1000): 0.827,
    (20, 100): 0.044, (20, 300): 0.284, (20, 500): 0.435, (20, 1000): 0.627,
    (40, 100): 0.000, (40, 300): 0.022, (40, 500): 0.091, (40, 1000): 0.278,
    (100, 1000): 0.002,
}


@pytest.mark.parametrize("key,expected", PUBLISHED.items())
def test_published_ruin_values(key, expected):
    units, hands = key
    assert risk_of_ruin(units, hands).ruin == pytest.approx(expected, abs=0.002)


def test_ruin_rises_with_hands():
    prev = -1.0
    for h in (100, 300, 500, 1000):
        r = risk_of_ruin(20, h).ruin
        assert r > prev
        prev = r


def test_ruin_falls_with_bankroll():
    prev = 2.0
    for u in (10, 20, 40, 100):
        r = risk_of_ruin(u, 500).ruin
        assert r < prev
        prev = r


def test_deep_bankroll_still_usually_loses():
    """Ruin ~0 does not mean profit: the point the calculator exists to make."""
    res = risk_of_ruin(100, 500)
    assert res.ruin < 0.001
    assert res.finished_ahead < 0.45


def test_player_side_is_worse_than_banker():
    b = risk_of_ruin(20, 1000, side="banker").ruin
    p = risk_of_ruin(20, 1000, side="player").ruin
    assert p > b
