"""The edge-evidence gate.

A strategy is *not* an edge because its backtest PnL is positive. It is a
candidate edge only when, simultaneously:

1. there are at least ``min_settled`` settled markets of evidence;
2. total post-fee PnL is positive;
3. the bootstrap confidence interval's lower bound on per-market mean PnL is
   strictly positive (resampled over *markets*, not fills -- fills within a
   market are correlated and resampling them individually overstates
   certainty);
4. mean closing-line value is strictly positive (you beat the close, not
   just the scoreboard).

Anything less is "keep researching", and this module will say so instead of
letting a green PnL number stand in for proof.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Sequence


@dataclass(frozen=True)
class EdgeEvidenceReport:
    n_settled: int
    post_fee_pnl: Decimal
    mean_market_pnl: Decimal | None
    ci_low: Decimal | None
    ci_high: Decimal | None
    clv_mean_cents: Decimal | None
    n_clv: int
    passed: bool
    reasons: tuple[str, ...]

    def summary(self) -> str:
        lines = [
            f"settled markets : {self.n_settled}",
            f"post-fee PnL    : ${self.post_fee_pnl}",
            (
                f"mean/mkt PnL    : ${self.mean_market_pnl} "
                f"[{self.ci_low}, {self.ci_high}] (bootstrap 95%)"
                if self.mean_market_pnl is not None
                else "mean/mkt PnL    : n/a"
            ),
            (
                f"CLV mean        : {self.clv_mean_cents}c over {self.n_clv} fills"
                if self.clv_mean_cents is not None
                else f"CLV mean        : n/a ({self.n_clv} fills)"
            ),
            f"verdict         : {'PASS' if self.passed else 'FAIL'}",
        ]
        for reason in self.reasons:
            lines.append(f"  - {reason}")
        return "\n".join(lines)


def _bootstrap_ci(
    values: Sequence[Decimal],
    *,
    n_boot: int,
    seed: int,
    alpha: float,
) -> tuple[Decimal, Decimal]:
    rng = random.Random(seed)
    floats = [float(v) for v in values]
    n = len(floats)
    means = sorted(
        sum(rng.choice(floats) for _ in range(n)) / n for _ in range(n_boot)
    )
    lo_idx = int((alpha / 2) * n_boot)
    hi_idx = min(n_boot - 1, int((1 - alpha / 2) * n_boot))
    quant = Decimal("0.0001")
    return (
        Decimal(str(means[lo_idx])).quantize(quant),
        Decimal(str(means[hi_idx])).quantize(quant),
    )


def evaluate(
    per_market_pnl: Mapping[str, Decimal],
    clv_cents: Sequence[Decimal],
    *,
    min_settled: int = 30,
    n_boot: int = 10_000,
    seed: int = 7,
    alpha: float = 0.05,
) -> EdgeEvidenceReport:
    reasons: list[str] = []
    pnls = list(per_market_pnl.values())
    n_settled = len(pnls)
    total = sum(pnls, Decimal("0"))

    if n_settled < min_settled:
        reasons.append(
            f"insufficient evidence: {n_settled} settled markets < required {min_settled}"
        )
    if total <= 0:
        reasons.append(f"post-fee PnL is not positive (${total})")

    mean_pnl = ci_low = ci_high = None
    if n_settled >= 2:
        mean_pnl = (total / Decimal(n_settled)).quantize(Decimal("0.0001"))
        ci_low, ci_high = _bootstrap_ci(pnls, n_boot=n_boot, seed=seed, alpha=alpha)
        if ci_low <= 0:
            reasons.append(
                f"bootstrap CI lower bound not positive ({ci_low}); "
                "the mean could plausibly be zero or negative"
            )
    else:
        reasons.append("too few settled markets to bootstrap a confidence interval")

    clv_mean = None
    if clv_cents:
        clv_mean = (sum(clv_cents, Decimal("0")) / Decimal(len(clv_cents))).quantize(
            Decimal("0.0001")
        )
        if clv_mean <= 0:
            reasons.append(
                f"mean CLV not positive ({clv_mean}c): fills do not beat the close"
            )
    else:
        reasons.append("no CLV evidence: cannot show fills beat the closing line")

    return EdgeEvidenceReport(
        n_settled=n_settled,
        post_fee_pnl=total,
        mean_market_pnl=mean_pnl,
        ci_low=ci_low,
        ci_high=ci_high,
        clv_mean_cents=clv_mean,
        n_clv=len(clv_cents),
        passed=not reasons,
        reasons=tuple(reasons),
    )
