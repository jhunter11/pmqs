from decimal import Decimal

from pmqs.validate import evaluate


def test_insufficient_settled_markets_fails() -> None:
    pnls = {f"M{i}": Decimal("1.00") for i in range(5)}
    report = evaluate(pnls, [Decimal("1")], min_settled=30)
    assert not report.passed
    assert any("insufficient evidence" in r for r in report.reasons)


def test_negative_pnl_fails() -> None:
    pnls = {f"M{i}": Decimal("-0.50") for i in range(40)}
    report = evaluate(pnls, [Decimal("1")], min_settled=30)
    assert not report.passed
    assert any("not positive" in r for r in report.reasons)


def test_missing_clv_fails_even_with_positive_pnl() -> None:
    pnls = {f"M{i}": Decimal("1.00") for i in range(40)}
    report = evaluate(pnls, [], min_settled=30)
    assert not report.passed
    assert any("no CLV evidence" in r for r in report.reasons)


def test_strong_consistent_evidence_passes() -> None:
    pnls = {f"M{i}": Decimal("1.00") + Decimal(i % 3) * Decimal("0.10") for i in range(40)}
    clv = [Decimal("2.0")] * 100
    report = evaluate(pnls, clv, min_settled=30)
    assert report.passed
    assert report.reasons == ()
    assert report.ci_low is not None and report.ci_low > 0


def test_high_variance_fails_ci_even_with_positive_mean() -> None:
    # Mean is positive but one enormous loss makes the CI cross zero.
    pnls = {f"M{i}": Decimal("1.00") for i in range(39)}
    pnls["M39"] = Decimal("-35.00")
    clv = [Decimal("2.0")] * 100
    report = evaluate(pnls, clv, min_settled=30)
    assert not report.passed
    assert any("lower bound" in r for r in report.reasons)


def test_deterministic_with_seed() -> None:
    pnls = {f"M{i}": Decimal(str((i % 7) - 2)) for i in range(40)}
    first = evaluate(pnls, [Decimal("1")], seed=42)
    second = evaluate(pnls, [Decimal("1")], seed=42)
    assert first.ci_low == second.ci_low
    assert first.ci_high == second.ci_high
