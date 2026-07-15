# Closing-Line Value: The Stat That Separates Luck from Information

Here is the most useful question in trading evaluation, and almost nobody
asks it of their backtest:

> Forget whether you won. Were your prices better than the market's final
> ones?

## Why the close is the benchmark

A prediction market's last price before settlement — the closing line — is
the sharpest estimate anyone had of the outcome's probability. It aggregates
every participant, including the ones smarter and faster than you, at the
moment of maximum information.

The outcome itself is just one draw from that probability. A 65% favorite
loses 35% of the time; a portfolio of them loses often enough that your PnL
over dozens of markets is mostly noise. But your fill price versus the close
is not noise — it's a direct measurement of whether you were *early to
information the market later agreed with*.

- Bought YES at 40c, market closed at 55c: **+15c of CLV.** Whatever the
  outcome, you knew (or moved) first.
- Bought YES at 60c, market closed at 55c: **−5c.** Even if you won, you
  were the person the close-movers profited from.

Positive CLV compounds across markets into exactly the thing PnL can't prove
on small samples: repeatability.

## The empirical teeth

This isn't theory to us. We trained a winner model for pro tennis on 62,768
matches with two decades of features, evaluated walk-forward (train on past
seasons, test on the next) against the de-vigged sharp closing line across
37,572 odds-present matches. The model was worse than the closing line in
**all nine test seasons** — pooled log-loss 0.59215 vs the line's 0.58843.
Nine for nine. The line had already priced everything our features knew, and
then some.

PnL evaluation would have needed years of betting volume to reveal this.
CLV-style evaluation revealed it in one afternoon and killed the strategy
before it cost anything. (The autopsy is written up in the PMQS Pro case-study
pack; the short version is above.)

## CLV on event contracts, concretely

Sign conventions are where implementations quietly break. The frame is
always: *positive = the close moved to the profitable side of your fill.*

```
buy  YES at v, close c (YES mid):  CLV = c − v
sell YES at v:                     CLV = v − c
NO-side fills: convert first (close_no = 100 − c), same buy/sell logic
```

Then average across fills and demand the mean be positive before you believe
anything. In [PMQS](https://github.com/jhunter11/pmqs), that's not optional:
mean CLV > 0 is one of the four conditions of the edge gate, computed on
every backtest from the last observable mid before each settlement
([pmqs/markout.py](../../src/pmqs/markout.py)).

## The caveats that keep it honest

- **CLV needs a fair close.** In thin markets the last quote can be a stale
  1-lot. PMQS uses the last snapshot with a *defined* mid; if your capture is
  sparse near settlement, treat CLV with suspicion (and fix the capture).
- **Positive CLV with negative PnL happens** — usually meaning fees and
  spread ate an edge that was real but too small. That's a cost problem, not
  an information problem; they have different fixes.
- **Negative CLV with positive PnL also happens** — that's the dangerous
  quadrant, the signature of running hot on variance. It fails the gate, and
  it should.

One line to take away: **the market's close is the exam; the settlement is
the party afterwards.** Grade yourself on the exam.
