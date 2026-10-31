import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "part_a"))

from A2_partA_manan import ab_test, capacity, funnel, normal_cdf


def test_capacity_and_ab_numbers_match_part_a_writeup():
    q = 0.75
    expected_attempts = sum(q**k for k in range(3))
    assert abs(expected_attempts - 2.3125) < 1e-9
    assert abs(1 - q**3 - 0.578125) < 1e-9
    assert abs(normal_cdf(0.0) - 0.5) < 1e-9

    buf = io.StringIO()
    with redirect_stdout(buf):
        capacity()
        ab_test()
        funnel()
    out = buf.getvalue()
    assert "674.5" in out
    assert "significant at 95% (two-sided)? True" in out
    assert "significant at 95% (two-sided)? False" in out
    assert "W2" in out
