"""End-to-end demo, no network and no API key required.

Generates a synthetic market stream, runs the deliberately edge-free
ThresholdScaffold through the conservative replayer, and prints the edge
gate's verdict -- which is FAIL, because synthetic prices are fair by
construction and "buy cheap YES" is not information.

That failing verdict is the product working correctly. Swap in your own
strategy and your own captured data; the gate's standards do not change.

    python examples/run_fixture_backtest.py
"""

from decimal import Decimal

from pmqs import (
    ConservativeFillModel,
    FeeSchedule,
    FixtureConfig,
    Replayer,
    ThresholdScaffold,
    generate_events,
)


def main() -> None:
    events = generate_events(FixtureConfig(n_markets=40, snapshots_per_market=60, seed=7))
    fill_model = ConservativeFillModel(
        fee_schedule=FeeSchedule(),
        latency_ms=500,
        size_haircut=Decimal("0.5"),
    )
    strategy = ThresholdScaffold(threshold_cents=35, quantity=20)
    result = Replayer(fill_model=fill_model, min_settled=30).run(events, strategy)
    print(result.summary())
    print()
    print("A FAIL verdict on this demo is correct behavior: synthetic data is")
    print("fair by construction, so no honest gate should bless this strategy.")


if __name__ == "__main__":
    main()
