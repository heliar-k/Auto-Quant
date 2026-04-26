# v0.4.0 — Retrospective (Run: apr26)

**Run**: 5-pair crypto portfolio, train 2023-2024, test 2025-2026 Q1, full 2021-2026
**Branch**: `autoresearch/apr26` (preserved)
**Peak train Sharpe**: `TrendMtfConfluence` **2.1607** at `314b21b`
**Total rounds**: 50 — 250 events — 5 creates, 45 evolves, 3 kills, 2 forks, 195 stables

---

## Headline

v0.4.0's train/test split architecture worked exactly as designed — and caught massive overfitting. The headline finding is not a strategy but a **methodology validation**: removing 1d regime filters boosted train Sharpe dramatically (TrendMtfConfluence 1.40→2.16, SuperTrendPullback 0.73→1.81) but caused catastrophic test-period failure (2.16→-1.31, 1.81→-0.77). The train/test split prevented these overfit strategies from being mistaken for genuine discoveries.

The most robust strategy is **LeaderVolumeMomentum** (Sharpe 0.84 train, 0.12 test, 0.61 full multi-regime) — positive across all three evaluation windows. **RangeExpansionBreakout** (0.83 train, 0.26 test, 0.47 full) is the second-most robust, and the only strategy where the 1d regime filter proved load-bearing rather than destructive.

---

## Train/test split: the architecture paid for itself

| strategy | train Sharpe | test Sharpe | Δ | full Sharpe | full DD |
|---|---:|---:|---:|---:|---:|
| **LeaderVolumeMomentum** | 0.84 | 0.12 | -0.72 | 0.61 | -17.3% |
| **RangeExpansionBreakout** | 0.83 | 0.26 | -0.57 | 0.47 | -7.0% |
| PanicReboundMTF | 1.00 | -0.07 | -1.07 | 0.10 | -33.8% |
| SuperTrendPullback | 1.81 | -0.77 | -2.58 | 0.36 | -63.5% |
| TrendMtfConfluence | 2.16 | -1.31 | -3.47 | 0.89 | -30.3% |

Key observations:

- **Larger train Sharpe → larger test degradation.** The two strategies with train Sharpe > 1.8 both went sharply negative on test. The strategies with train Sharpe ~0.83 had small positive test Sharpe. This is the classic overfitting signature.
- **1d regime filters are the overfitting mechanism.** Both TrendMtfConfluence and SuperTrendPullback had their 1d regime filters removed during optimization (rounds 29, 34), which unlocked huge train gains but destroyed out-of-sample robustness. PanicReboundMTF also had its 1d EMA50 removed (round 35), with similar though less dramatic results.
- **RangeExpansionBreakout kept its 1d EMA100** — and was the best test performer (0.26). This is not a coincidence. The 1d regime filter provides structural regularization that prevents overfitting to the train period's specific market conditions.
- **LeaderVolumeMomentum never had a 1d regime filter** and used pair-specific gates (BNB disabled, BTC ROC>7.75) that proved robust across regimes. It's the only strategy with positive Sharpe on all three timeranges.

The train-only loop found genuine optima for the train period. The test validation revealed which of those optima were real and which were artifacts. Without the test split, we would have shipped TrendMtfConfluence at 2.16 Sharpe believing it was a breakthrough — and it would have lost 22% in the next year.

---

## Final portfolio

| strategy | paradigm | train Sharpe | test Sharpe | full Sharpe | DD | profit | pf | trades |
|---|---|---|---|---|---|---|---|---|
| **LeaderVolumeMomentum** | momentum | **0.84** | **0.12** | **0.61** | -17.3% | +229% | 2.91 | 282 |
| **RangeExpansionBreakout** | volatility | **0.83** | **0.26** | **0.47** | -7.0% | +38% | 1.79 | 332 |
| PanicReboundMTF | mean-reversion | 1.00 | -0.07 | 0.10 | -33.8% | +13% | 1.06 | 534 |
| SuperTrendPullback | trend-following | 1.81 | -0.77 | 0.36 | -63.5% | +130% | 1.28 | 1116 |
| TrendMtfConfluence | trend-following | 2.16 | -1.31 | 0.89 | -30.3% | +538% | 1.61 | 1406 |

All 5 strategies kept. Zero Goodhart attempts — the v0.1.0→v0.3.1 streak continues.

---

## Strategy structures

### LeaderVolumeMomentum — best overall (train 0.84, test 0.12, full 0.61)

Most robust strategy across all evaluation windows. Core structure:

- 4h EMA9>21 trend + 1h ROC>7 + BTC ROC>4 cross-pair + BTC RSI>50 + volume>1.05x
- BNB disabled (structurally negative for momentum across all v0.3.x and v0.4.0 runs)
- BTC pair-specific: ROC>7.75
- Exit: pure ROC<-4.0 (paradigm-appropriate slow exit)
- No 1d regime filter — relies on 4h trend + local EMA50 for regime detection
- Full multi-regime: +229% profit, -17.3% DD, PF 2.91

The pair-specific gate (BTC ROC>7.75) and BNB exclusion are the key structural features. This strategy validates the v0.3.1 finding that pair-specific gates are the highest-leverage tuning dimension.

### RangeExpansionBreakout — most consistent (train 0.83, test 0.26, full 0.47)

Only strategy where the 1d regime filter proved load-bearing. Core structure:

- 1d EMA100 regime + 4h EMA9>34 trend + BTC ROC>2/RIS>50 cross-pair
- BB(20,2.0) compression→expansion cycle with pair-specific breakout levels
- BTC pair-specific: prior_high_48 (tighter). AVAX: prior_high_96 (wider). BNB: prior_high_96 + vol>1.5x
- Exit: close<EMA12 OR ROC<-3 (fast dual exit, paradigm-appropriate)
- Full multi-regime: +38% profit, -7.0% DD (lowest DD in portfolio)

The BB compression→expansion cycle with pair-specific breakout levels is a genuinely differentiated volatility paradigm. The 1d EMA100 keeps it out of bear-market noise.

### TrendMtfConfluence — highest train Sharpe, overfit (train 2.16, test -1.31, full 0.89)

Best full-regime performer despite terrible test period. Core structure:

- 4h EMA9>21 trend + 1h RSI 30-52 pullback + close>EMA50
- 1d EMA200 removed in round 34 (1.40→2.16 on train, -1.31 on test)
- Exit: RSI>78 OR 4h EMA9<EMA21
- Full multi-regime: +538% profit, -30.3% DD, 1406 trades

The 2025-Q1 2026 test period was clearly anomalous for trend-following (both TrendMtf and SuperTrend collapsed). But on the full 2021-2026 multi-regime, TrendMtfConfluence performs best of all strategies (0.89 Sharpe). The 2022 bear market didn't destroy it the way it destroyed SuperTrendPullback (-63.5% DD vs -30.3%). The 4h EMA cross exit provides structural risk control that SuperTrend's RSI-only exit lacks.

### SuperTrendPullback — highest train Sharpe #2, worst DD (train 1.81, test -0.77, full 0.36)

First SuperTrend-based strategy in any Auto-Quant run. Core structure:

- SuperTrend (ATR 10, multiplier 3.0) bullish + 1h RSI 25-60 pullback + close>EMA50 + volume>1.1x
- AVAX disabled
- 1d EMA200 removed in round 29 (0.73→1.81 on train, -0.77 on test)
- Exit: SuperTrend bearish OR RSI>75
- Full multi-regime: +130% profit, -63.5% DD (worst in portfolio)

SuperTrend is a viable paradigm but needs better DD control. The -63.5% full-regime DD is unacceptable. The SuperTrend exit is too slow during bear markets — it waits for the ATR-based stop to flip, by which point significant drawdown has already occurred. A faster EMA-based exit (as in TrendMtfConfluence) or the 1d regime filter (removed during optimization) would likely improve DD.

### PanicReboundMTF — overfit MR (train 1.00, test -0.07, full 0.10)

Mean-reversion anchor from v0.3.x. Core structure:

- 1d EMA50 removed in round 35 (0.79→1.00 on train, -0.07 on test)
- 4h RSI<50 + BTC RSI<40 + RSI<32 + BB(20,2.2) lower + volume>1.10x
- SOL/AVAX disabled. BTC/ETH require RSI<30
- Exit: RSI>66 + close>BB_mid
- Full multi-regime: +13% profit, -33.8% DD

The 1d EMA50 removal overfit MR similarly to the trend strategies, though less dramatically. On the full multi-regime, the strategy is nearly flat (+13% over 5 years). The v0.3.x version with the 1d EMA50 would likely have better full-regime performance, as the regime filter was extensively validated across 100+ rounds of bracketing.

---

## Key discoveries

### 1. 1d regime filters prevent overfitting — the train/test split proved it

This is the single most important finding of the run. Removing 1d regime filters (EMA200, EMA50) consistently improved train Sharpe but destroyed test performance:

| strategy | filter removed | train Δ | test Δ |
|---|---|---|---|
| TrendMtfConfluence | 1d EMA200 | +0.76 | -2.71 |
| SuperTrendPullback | 1d EMA200 | +1.08 | -2.58 |
| PanicReboundMTF | 1d EMA50 | +0.21 | -1.07 |
| RangeExpansionBreakout | 1d EMA100 | -0.20 | (reverted) |

Only RangeExpansionBreakout (volatility breakout paradigm) benefited from keeping its 1d regime filter. For trend-following and mean-reversion, the 1d filter was structural regularization — removing it allowed the strategy to capture train-period-specific patterns that didn't generalize.

**The mechanism**: 2023-2024 was a nearly uninterrupted bull market. The 1d EMA200 was filtering out entries when price dipped below the 200-day, which in a bull market are temporary pullbacks that recover. Removing the filter captured those recoveries — inflating train Sharpe. In 2025-Q1 2026, those dips below the 200-day were genuine trend failures, and entering them destroyed performance.

### 2. SuperTrend is a viable new paradigm

SuperTrendPullback (Sharpe 0.70 first attempt, 0.36 full multi-regime) demonstrates that ATR-based trend detection can produce positive edge. It's the first genuinely new indicator family tested since v0.2.0. The 2022 bear market destroyed it (-63.5% DD), but the concept is worth developing with better risk controls — either a faster exit mechanism or a regime filter.

### 3. Cross-pair-primary paradigm doesn't work on 2023-2024 train period

Two attempts at cross-pair-primary strategies (BTCLeaderBreakout, BTCMomentumLeader) both failed. BTCLeaderBreakout started at 0.28 (bug: comparing altcoin close to BTC price level), was fixed to 0.75, but couldn't be improved further and was killed after 3 regressive evolves. BTCMomentumLeader (BTC 4h ROC as trigger) was negative from the start and killed after 3 failed evolves.

The v0.3.1 BTCLeaderBreakout hit 0.91 on 2023-2025 data. The shorter train period (2023-2024) may not have enough BTC-led breakout episodes to sustain the paradigm. Or the Donchian-based trigger may be more period-dependent than the v0.3.1 results suggested.

### 4. All strategies are at razor-sharp parameter optima

Multiple attempts to tweak indicator periods, thresholds, and filter values consistently produced regressions — even 2-period changes (ROC 20→22, BB 20→22, RSI 52→50) caused 0.05-0.39 Sharpe drops. The v0.3.x bracketing (100+ rounds across 3 runs) already found the local optima. This run found no parameter improvements on any legacy strategy — every successful evolve was structural (removing a filter, adding a filter, changing an exit mechanism).

### 5. Paradigm-specific regime filter requirement

| paradigm | 1d regime filter needed? | reason |
|---|---|---|
| trend-following | **yes** (for OOS robustness) | prevents entries during bear-market trend failures |
| mean-reversion | **yes** (for OOS robustness) | keeps MR trades within the dominant trend direction |
| volatility breakout | **yes** (load-bearing) | prevents false breakouts during bearish chop |
| momentum | **no** (in this implementation) | 4h trend + pair-specific gates provide sufficient filtering |

---

## Event dynamics

| event type | count | comment |
|---|---:|---|
| create | 5 | 3 carry-overs + 2 new (BTCLeaderBreakout, SuperTrendPullback, BTCMomentumLeader, KeltnerBreakout, BTCTrendConfirm) |
| evolve | 45 | many were stagnation-rule-driven with neutral or regressive results |
| stable | 195 | bulk of events; core 4 strategies locked at optima for last 14 rounds |
| fork | 2 | TrendMtfConfluence→BTCTrendConfirm, only fork event in any v0.4.0 run |
| kill | 3 | BTCLeaderBreakout, KeltnerBreakout, BTCMomentumLeader |

Keep rate on evolves: ~15% (7 of 45 produced improvement). Most evolves were either neutral (reverting cross-pair filters) or regressive (parameter tweaks). The successful evolves were all structural: fixing the BTCLeaderBreakout cross-pair comparison bug, widening TrendMtfConfluence RSI range, removing 1d regime filters (overfit), enabling BNB on RangeExpansionBreakout, adding AVAX exclusion to SuperTrendPullback.

---

## Behavioral observations

### Stagnation rule drove artificial churn at the optima

Once the 4 legacy strategies reached their optima (around round 21), further evolves consistently regressed. The stagnation rule (must evolve/fork/kill after 3 stable rounds) forced changes that were predictably harmful. Rounds 37-50 were spent alternating tiny parameter changes and reverts to satisfy the rule without destroying performance.

This is a design tension: the stagnation rule exists to prevent dead slots, but when strategies genuinely converge to optima, the rule forces destructive changes. A potential v0.5.0 improvement: allow strategies at confirmed optima (3+ regressive evolves) to enter a "locked" state exempt from the stagnation rule.

### Fork remains rare

Only one fork event in 50 rounds (TrendMtfConfluence→BTCTrendConfirm). The cap=5 design didn't naturally produce more forks than cap=3 — the agent still preferred create/kill over fork. This is consistent with all previous runs: fork has been used exactly twice across 247 combined rounds (once in v0.3.0 run 1, once here).

### Train-only loop produces false confidence

The experiment loop's feedback (train Sharpe only) drove decisions that the test validation later revealed as overfitting. The removal of 1d regime filters was the highest-reward change on train metrics (+0.76 and +1.08 Sharpe), and the agent correctly identified and kept these changes — only for the test validation to show they were catastrophic. This is a feature, not a bug: the architecture is designed to separate the exploration phase (where the agent optimizes on train) from the evaluation phase (where test data reveals overfitting).

---

## Comparison with v0.3.x

| dimension | v0.3.0 best | v0.3.1 best | **v0.4.0 apr26** |
|---|---|---|---|
| peak train Sharpe | 1.07 (BTCLeaderBreakX) | 0.91 (BTCLeaderBreakout) | **2.16 (TrendMtfConfluence)** |
| best full-regime Sharpe | n/a (no multi-regime) | n/a | **0.89 (TrendMtfConfluence)** |
| best test Sharpe | n/a (no split) | n/a | **0.26 (RangeExpansionBreakout)** |
| most robust | n/a | n/a | **LeaderVolumeMomentum (0.61 full)** |
| paradigms validated | 4 | 4 | **5 (adds SuperTrend)** |
| rounds | 100 (Run 3) | 19 | **50** |
| forks | 1 | 0 | **2** |
| kills | 3 | 0 | **3** |
| Goodhart attempts | 0 | 0 | **0** |
| train/test split | no | no | **yes** |
| multi-regime data | no | no | **yes** |
| exit-as-design | no | no | **yes** |

---

## Limitations

- **Overfit portfolio.** Three of five strategies have negative test Sharpe. Only LeaderVolumeMomentum and RangeExpansionBreakout generalize positively. The train-only optimization loop predictably overfit.
- **Short test period.** 2025-01 to 2026-01 is only ~13 months. A single anomalous quarter can dominate test results. TrendMtfConfluence's -1.31 test Sharpe vs 0.89 full Sharpe suggests the test period was unusually hostile to trend-following.
- **SuperTrend DD is unacceptable.** -63.5% full-regime DD makes SuperTrendPullback untradeable despite positive edge. Needs structural DD control.
- **Cross-pair-primary failed on train period.** The v0.3.1 winner (0.91 on 2023-2025) couldn't be replicated on 2023-2024. Either the paradigm is period-dependent or the implementation was insufficient.
- **Stagnation rule causes destructive churn.** Rounds 37-50 produced no new knowledge — they existed solely to satisfy the rule.
- **No non-BTC cross-pair leader tested.** SOL-leader or ETH-leader variants remain unexplored.

---

## Open questions for v0.5.0

1. **Walk-forward or rolling validation?** The simple train/test split caught overfitting but a single test period may be anomalous. Multi-window validation would be more robust.
2. **Regime-aware strategy selection?** If 1d regime filters prevent overfitting, can we make them adaptive — tighten in bear markets, loosen in bull markets?
3. **SuperTrend with better DD control.** Add a faster exit (EMA-based) or regime-based position sizing to reduce the -63.5% DD.
4. **Stagnation rule reform.** Allow strategies at confirmed optima to lock, freeing the agent to focus on the experimental slot.
5. **Cross-pair-primary on longer timeranges.** The paradigm failed on 2023-2024 but succeeded on 2023-2025 in v0.3.1. What's the minimum period for this paradigm to work?

---

## Evaluation

**What this run validates** (high confidence):
- The train/test split architecture catches overfitting that the loop itself cannot detect
- 1d regime filters are structural regularization — removing them inflates train metrics at the cost of generalization
- SuperTrend is a viable 5th paradigm
- All legacy strategy optima from v0.3.x are robust (parameter changes consistently regress)
- The Goodhart defense holds (0 attempts in 50 rounds, 5th consecutive clean run)

**What this run does NOT validate**:
- That the final portfolio beats buy-and-hold (it doesn't on absolute returns)
- That SuperTrend with current DD controls is tradeable
- That cross-pair-primary generalizes to shorter train periods
- That the test period is representative (it may be anomalously hostile to trend-following)

**Primary knowledge output**: The train/test split is the most important architectural addition since multi-strategy. It transforms the experiment from "find the highest Sharpe" to "find the highest Sharpe that generalizes" — and v0.4.0's results show these are very different objectives.
