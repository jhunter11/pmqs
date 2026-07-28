#!/usr/bin/env python3
"""The way in.

    python3 explore.py        interactive menu
    python3 explore.py 3      run one item and exit
    python3 explore.py all    run everything, top to bottom

Works from a bare checkout with nothing installed — pmqs has zero third-party
dependencies, and this script puts src/ on the path for itself and for anything
it launches. Only the test suite needs pytest.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
sys.path.insert(0, SRC)

# Child processes get the same path, so the whole menu works from a bare
# checkout with nothing installed.
CHILD_ENV = dict(os.environ)
CHILD_ENV["PYTHONPATH"] = os.pathsep.join(
    [SRC] + ([CHILD_ENV["PYTHONPATH"]] if CHILD_ENV.get("PYTHONPATH") else [])
)

WIDTH = min(shutil.get_terminal_size((84, 24)).columns, 84)
_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code, s):
    return f"\033[{code}m{s}\033[0m" if _COLOR else s


def bold(s): return _c("1", s)
def dim(s): return _c("2", s)
def cyan(s): return _c("36", s)
def green(s): return _c("32", s)
def red(s): return _c("31", s)


def header(title):
    print()
    print(bold(title))
    print(dim("─" * min(len(title), WIDTH)))


def rule(label=""):
    if not label:
        print(dim("─" * (WIDTH - 2)))
    else:
        print(dim(f"── {label} " + "─" * max(WIDTH - len(label) - 6, 2)))


def note(text):
    for line in textwrap.wrap(text, WIDTH - 2):
        print(dim(line))


def bullet(text):
    lines = textwrap.wrap(text, WIDTH - 6)
    for i, line in enumerate(lines):
        print(f"  {'·' if i == 0 else ' '} {line}")


def need_pmqs():
    try:
        import pmqs  # noqa: F401
        return True
    except ImportError:
        print(red("  pmqs is not importable, which should not happen —"))
        print(red(f"  expected the package under {SRC}"))
        print()
        bullet("pip install -e .")
        return False


# ==========================================================================


def item_overview():
    header("What this is")
    note(
        "Most prediction-market backtests are fiction. They fill at mid with "
        "no latency, ignore fees, resample correlated fills as if they were "
        "independent, and quietly peek at the future. Then the bot goes live "
        "and the edge evaporates into spread and fees."
    )
    print()
    note(
        "PMQS makes those shortcuts structurally impossible, and adds a gate "
        "that answers 'is this an edge?' with 'no' by default. The bundled "
        "demo strategy fails that gate on purpose. If a tool never says no, "
        "it isn't validation."
    )
    print()
    rule("the four things it refuses to let you do")
    print()
    bullet("Fill at mid. Fills cross the spread, take a size haircut on "
           "displayed liquidity, and never get price improvement.")
    bullet("Trade instantly. Orders execute against the book after your "
           "configured latency — a backdated order raises a lookahead error.")
    bullet("Forget fees. Conservative cent-ceiling rounding by default, with "
           "per-series rates.")
    bullet("Resample fills. The bootstrap clusters by settled market, because "
           "fills inside one market are correlated.")
    print()
    rule("what it will never ship")
    print()
    note(
        "No signals, no picks, no performance claims, no bundled market data, "
        "and no live order placement. It is research infrastructure. The "
        "included strategy is deliberately edge-free."
    )


def item_gate():
    header("The gate")
    note(
        "Four conditions, all of them, or the verdict is FAIL with reasons. "
        "The bar is high on purpose: a green P&L number is the weakest form "
        "of evidence there is."
    )
    print()
    for cond, why in [
        ("≥ 30 settled markets",
         "a floor, not a target — see docs/posts/07"),
        ("positive post-fee P&L",
         "gross is not a result"),
        ("bootstrap CI lower bound > 0",
         "clustered by market, not by fill"),
        ("positive mean closing-line value",
         "beating the scoreboard once is luck; beating the close is not"),
    ]:
        print(f"  {cyan('▸')} {cond:34s} {dim(why)}")
    print()
    note(
        "The default answer is no. The gate exists to make a yes mean "
        "something. Full methodology: docs/validation-playbook.md"
    )


def item_demo():
    header("Watch the demo strategy fail its own gate")
    note(
        "A synthetic market stream, generated fair by construction, run "
        "through the conservative replayer with a deliberately edge-free "
        "'buy cheap YES' strategy. No network, no API key."
    )
    if not need_pmqs():
        return
    print()
    sys.stdout.flush()   # keep our output ahead of the child's when piped
    subprocess.run([sys.executable, os.path.join(HERE, "examples",
                                                 "run_fixture_backtest.py")],
                   cwd=HERE, env=CHILD_ENV)
    print()
    note(
        "That FAIL is the product working. Synthetic prices carry no "
        "information, so no honest gate should bless a strategy trading them."
    )


def item_orderbook():
    header("The orderbook model, and why it rejects things")
    note(
        "Kalshi quotes two bid ladders — YES and NO — and asks are derived: a "
        "NO bid at p is a YES ask at 100−p. Getting this wrong is the quiet "
        "source of a lot of fake edge, so the model refuses malformed input "
        "rather than repairing it."
    )
    if not need_pmqs():
        return

    from pmqs import BookLevel, FeeSchedule, OrderbookSnapshot

    print()
    book = OrderbookSnapshot(
        ts_ms=1_700_000_000_000,
        market="DEMO",
        yes_bids=(BookLevel(40, 500), BookLevel(39, 900)),
        no_bids=(BookLevel(57, 400), BookLevel(56, 800)),
    )
    print(f"  market            {book.market}")
    print(f"  YES bid / ask     {book.best_yes_bid()} / {book.best_yes_ask()}c"
          f"   {dim('(the ask is derived from the NO bid at 57)')}")
    print(f"  YES mid           {book.yes_mid()}c")
    print(f"  spread            {book.spread_cents()}c")
    print()

    rule("now try to feed it something dishonest")
    print()
    def snap(**kw):
        return OrderbookSnapshot(ts_ms=1, market="DEMO", **kw)

    # Lazy, because some of these fail while the level is being constructed.
    cases = [
        ("a crossed book — YES bid 60 and NO bid 45 sum past 100",
         lambda: snap(yes_bids=(BookLevel(60, 100),), no_bids=(BookLevel(45, 100),))),
        ("a bid ladder that isn't sorted best-first",
         lambda: snap(yes_bids=(BookLevel(39, 100), BookLevel(40, 100)))),
        ("a duplicated price level",
         lambda: snap(yes_bids=(BookLevel(40, 100), BookLevel(40, 200)))),
        ("a price outside the tradeable 1-99c range",
         lambda: snap(yes_bids=(BookLevel(0, 100),))),
        ("a level with no size behind it",
         lambda: snap(yes_bids=(BookLevel(40, 0),))),
    ]
    for label, build in cases:
        try:
            build()
            print(f"  {red('✗ accepted')}  {label}")
        except ValueError as exc:
            print(f"  {green('✓ rejected')}  {label}")
            for line in textwrap.wrap(str(exc), WIDTH - 16):
                print(f"              {dim(line)}")
    print()
    note(
        "None of these is repaired into something plausible. A backtest that "
        "silently fixes a crossed book has just invented liquidity that was "
        "never there."
    )
    print()

    rule("fees are charged, and rounded against you")
    print()
    fees = FeeSchedule()
    for price in (10, 25, 50, 75, 90):
        fee = fees.fill_fee(contracts=100, price_cents=price, market="DEMO")
        print(f"  100 contracts at {price:2d}c    taker fee ${fee}")
    print()
    note(
        "Fees peak at 50c, where the contract is most uncertain — which is "
        "exactly where a naive strategy concentrates its trades. Rounding is "
        "cent-ceiling by default: against you, never for you."
    )


def item_lookahead():
    header("Latency is enforced, not assumed")
    note(
        "The replayer executes an order against the book that exists after "
        "your configured delay — never the book your signal saw. An order "
        "timestamped before the event that triggered it is a lookahead error, "
        "raised rather than silently filled."
    )
    if not need_pmqs():
        return
    print()
    rule("the relevant source")
    print()
    path = os.path.join(HERE, "src", "pmqs", "replay.py")
    with open(path) as fh:
        lines = fh.read().splitlines()
    hits = [i for i, l in enumerate(lines) if "lookahead" in l.lower()]
    for i in hits[:3]:
        lo, hi = max(0, i - 4), min(len(lines), i + 4)
        for n in range(lo, hi):
            marker = cyan("▸") if n == i else " "
            print(f"  {marker} {dim(f'{n + 1:4d}')}  {lines[n][:WIDTH - 12]}")
        print()
    note(f"src/pmqs/replay.py — {len(lines)} lines")


def item_posts():
    header("The field guide")
    note(
        "The reasoning behind each design choice, written up as short posts. "
        "They are the argument; the code is the enforcement."
    )
    print()
    d = os.path.join(HERE, "docs", "posts")
    for name in sorted(os.listdir(d)):
        if not name.endswith(".md") or name == "README.md":
            continue
        with open(os.path.join(d, name)) as fh:
            title = fh.readline().lstrip("# ").strip()
        print(f"  {cyan(name[:2])}  {title[:WIDTH - 8]}")
    print()
    note("docs/posts/ — start with 01, or 08 for the post-mortem of a stale "
         "feed manufacturing a fake edge.")


def item_tests():
    header("The test suite")
    note("Zero dependencies beyond pytest. If pytest isn't available, the "
         "modules still import and the demo still runs.")
    print()
    sys.stdout.flush()
    r = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                       cwd=HERE, env=CHILD_ENV)
    if r.returncode != 0:
        print()
        note("If pytest itself is missing: pip install pytest")


def item_source():
    header("Where everything is")
    print()
    for path, what in [
        ("src/pmqs/orderbook.py", "Kalshi-native book; asks derived, not quoted"),
        ("src/pmqs/fees.py", "fee math, conservative rounding, per-series rates"),
        ("src/pmqs/fills.py", "taker-only fills; cross the spread, haircut size"),
        ("src/pmqs/replay.py", "enforced latency; lookahead raises"),
        ("src/pmqs/ledger.py", "positions, cash, settlement, per-market P&L"),
        ("src/pmqs/markout.py", "markout horizons and closing-line value"),
        ("src/pmqs/validate.py", "the gate — four conditions, all of them"),
        ("src/pmqs/capture.py", "bring-your-own-key REST capture to JSONL"),
        ("src/pmqs/fixtures.py", "deterministic synthetic markets for tests"),
        ("docs/validation-playbook.md", "the full methodology"),
        ("docs/posts/", "the field guide, eight posts"),
    ]:
        p = os.path.join(HERE, path)
        n = ""
        if os.path.isfile(p) and p.endswith(".py"):
            n = f"  ({sum(1 for _ in open(p))} lines)"
        print(f"  {path:30s} {dim(what)}{dim(n)}")


MENU = [
    ("The short version", item_overview, ""),
    ("The gate — four conditions, all of them", item_gate, ""),
    ("Watch the demo fail its own gate", item_demo, "live"),
    ("The orderbook, and what it rejects", item_orderbook, "live"),
    ("Latency is enforced, not assumed", item_lookahead, ""),
    ("The field guide", item_posts, ""),
    ("Run the test suite", item_tests, "live"),
    ("Where everything is", item_source, ""),
]


def show_menu():
    print()
    print(bold("  PMQS — Prediction Market Quant Stack"))
    print(dim("  Execution-aware backtesting, and a gate that says no by default."))
    print()
    for i, (label, _, tag) in enumerate(MENU, 1):
        suffix = dim(f"   {tag}") if tag else ""
        print(f"   {cyan(str(i))}  {label}{suffix}")
    print(f"   {cyan('q')}  quit")
    print()


def run(choice):
    choice = choice.strip().lower()
    if choice in ("q", "quit", "exit", "0"):
        return False
    if choice == "all":
        for _, fn, _ in MENU:
            fn()
            print()
        return True
    if choice.isdigit() and 1 <= int(choice) <= len(MENU):
        MENU[int(choice) - 1][1]()
        return True
    print(dim(f"  no item {choice!r} — pick 1-{len(MENU)} or q"))
    return True


def main(argv):
    if len(argv) > 1:
        run(argv[1])
        return 0
    if not sys.stdin.isatty():
        show_menu()
        print(dim("  not a terminal — run `python3 explore.py <n>` to pick an item"))
        return 0
    while True:
        show_menu()
        try:
            choice = input("  > ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not run(choice):
            return 0
        print()
        try:
            input(dim("  ↵ back to the menu "))
        except (EOFError, KeyboardInterrupt):
            print()
            return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
