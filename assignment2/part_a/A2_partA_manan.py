from math import erf, sqrt


def normal_cdf(z: float) -> float:
    return 0.5 * (1 + erf(z / sqrt(2)))


# A1. Capacity planning
def capacity(accounts=200_000, max_attempts=3, p_connect=0.25,
             connected_secs=120, unanswered_secs=30, day_hours=10):
    q = 1 - p_connect
    # attempt k happens only if the previous k-1 attempts all failed
    exp_attempts = sum(q ** k for k in range(max_attempts))
    p_ever_connected = 1 - q ** max_attempts
    exp_unanswered = exp_attempts - p_ever_connected
    secs_per_account = p_ever_connected * connected_secs + exp_unanswered * unanswered_secs

    total_secs = accounts * secs_per_account
    avg_lines = total_secs / (day_hours * 3600)
    with_3_sigma = avg_lines + 3 * sqrt(avg_lines)

    print("A1 capacity")
    print(f"  expected attempts/account     {exp_attempts:.4f}")
    print(f"  P(connected)                  {p_ever_connected:.4f}")
    print(f"  expected unanswered/account   {exp_unanswered:.4f}")
    print(f"  line-seconds/account          {secs_per_account:.2f}")
    print(f"  total line-seconds            {total_secs:,.0f}")
    print(f"  average concurrent lines      {avg_lines:.1f}")
    print(f"  average + 3 sigma             {with_3_sigma:.1f}")
    print(f"  plan with +20% headroom       {avg_lines * 1.2:.0f}")
    print()


# A2. Two-proportion z-test
def two_proportion_z(success_a, n_a, success_b, n_b, label):
    p_a, p_b = success_a / n_a, success_b / n_b
    pooled = (success_a + success_b) / (n_a + n_b)
    se = sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = (p_b - p_a) / se
    one_sided = 1 - normal_cdf(z)          # H1: B > A
    two_sided = 2 * (1 - normal_cdf(abs(z)))

    print(f"A2 {label}")
    print(f"  A {p_a:.3%}   B {p_b:.3%}   pooled {pooled:.3f}   SE {se:.5f}")
    print(f"  z = {z:.3f}   one-sided p = {one_sided:.4f}   two-sided p = {two_sided:.4f}")
    print(f"  significant at 95% (two-sided)? {two_sided < 0.05}")
    print()


def ab_test(connected=4000, ptp_a=880, ptp_b=960, kept_rate_a=0.60, kept_rate_b=0.50):
    two_proportion_z(ptp_a, connected, ptp_b, connected, "PTP rate")
    kept_a = round(ptp_a * kept_rate_a)
    kept_b = round(ptp_b * kept_rate_b)
    two_proportion_z(kept_a, connected, kept_b, connected,
                     f"kept PTP per connected call (A={kept_a}, B={kept_b})")


# A3. Funnel step rates
def funnel():
    weeks = {
        "W1": (50_000, 12_500, 10_000, 2_500, 1_500),
        "W2": (50_000, 12_400, 7_400, 2_200, 1_300),
        "W3": (52_000, 13_000, 7_500, 2_250, 1_350),
    }
    print("A3 funnel   connect   rpc/conn   ptp/rpc   paid/ptp   paid/dialed")
    for week, (dialed, conn, rpc, ptp, paid) in weeks.items():
        print(f"  {week}       {conn/dialed:6.1%}    {rpc/conn:6.1%}    {ptp/rpc:6.1%}"
              f"    {paid/ptp:6.1%}     {paid/dialed:6.2%}")


if __name__ == "__main__":
    capacity()
    ab_test()
    funnel()