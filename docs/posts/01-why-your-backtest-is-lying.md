# Why Your Kalshi Bot's Backtest Is Lying to You

You wrote a strategy. You backtested it. The PnL curve goes up and to the
right. You're about to fund an account.

Before you do: your backtest is probably lying to you, and it's lying in six
specific, fixable ways. We know because we've shipped every one of these bugs
ourselves — and because the fix for each one is mechanical, not clever.

## 1. You didn't pay fees

The widely published taker fee curve on Kalshi-style venues is
`0.07 × contracts × P × (1−P)` — a parabola peaking at **1.75 cents per
contract at 50c**, rounded *up*. A strategy that trades near the middle of
the book pays the venue relentlessly: a round trip at 50c costs about 3.5c in
fees alone before you count the spread. Small "edges" of 2–3 cents — the size
most naive signals produce — are simply donations with extra steps.

And it cuts both ways: we once nearly killed a real strategy because a
backtest charged a flat 7% of stake instead of the actual curve (which is
~1.1–1.7% of stake at that strategy's prices). Wrong fee math corrupts the
verdict in whichever direction it's wrong.

## 2. You filled at mid

There is no mid. There's a bid and an ask, and as a taker you pay the ask
and receive the bid. A backtest that fills at mid hands every trade a phantom
half-spread of profit. At a typical 2-cent spread, that's a full cent per
trade of fiction — often bigger than the signal being tested.

## 3. You filled instantly

Your signal was computed on a book. By the time your order reaches the venue,
that book is gone — and the fills you get come from the book that exists
*after* your latency. For fast-moving markets (crypto brackets especially),
the book that exists after your latency has already incorporated the very
move you thought you predicted. When we benchmarked our own loop on
short-horizon BTC markets, model compute was ~0.6 microseconds and the
network round trip was ~34 milliseconds: the market always got to move last.

## 4. You got unlimited size

Displayed size is not your size. Some of it cancels before you arrive. Some
sits ahead of you in queue. And what remains selects for moments the market
is moving against you. If your backtest fills your full order at level one
every time, your capacity estimate is fantasy — we've watched a strategy's
paper PnL scale *linearly* with an assumed depth cap, which meant the "PnL"
was really just a measurement of the assumption.

## 5. You counted correlated fills as independent evidence

Twenty fills in one market are not twenty observations. They resolve with
**one** settlement — one coin flip, sized into twenty pieces. Bootstrap your
confidence interval over fills and it shrinks by roughly √(fills per market)
below its honest width. The correct unit of evidence is the settled market.

## 6. You beat the scoreboard, not the close

Winning trades at prices *worse* than the market's closing consensus is what
luck looks like. Being systematically on the right side of the close —
positive closing-line value — is what information looks like. This is the
oldest robust result in betting research, and it is brutal: we once trained a
model on 62,768 tennis matches and it lost to the closing line in **all nine**
walk-forward test seasons. The scoreboard would have taken years to tell us;
CLV said it immediately.

## The fix is structural, not motivational

You will not fix these by promising to be careful. Fix them by using
infrastructure where the lies are *impossible to express*:

- fills are taker-only, against displayed liquidity, with a size haircut;
- orders execute against the post-latency book; backdated orders **raise**;
- fees are charged per fill at conservative rounding;
- evidence is per-settled-market; the CI is clustered;
- CLV is measured on every backtest, and the gate requires it positive.

That's what [PMQS](https://github.com/jhunter11/pmqs) is — a small,
zero-dependency, MIT-licensed Python core where the demo strategy **fails its
own gate**, on purpose, with reasons:

```
verdict         : FAIL
  - post-fee PnL is not positive ($-37.23)
  - bootstrap CI lower bound not positive (-2.4622)
  - mean CLV not positive (-3.2222c): fills do not beat the close
```

If a tool never says no, it isn't validation. Run it yourself in 60 seconds,
no API key, no network: `python examples/run_fixture_backtest.py`.
