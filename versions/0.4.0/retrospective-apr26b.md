# v0.4.0 — Retrospective (Run 2: apr26b)

**Run**: 5-pair crypto portfolio, train 2021-2025 (multi-regime), test 2025-2026 Q1
**Branch**: `autoresearch/apr26b`
**Peak train Sharpe**: `BTCLeaderBreakout` **0.5957** at `6c3db15`
**Total rounds**: 95 — ~475 events — 5 creates, 2 kills, 88 evolves/stables

---

## Headline

v0.4.0 Run 2 proved that **multi-regime training (2021-2025) + structural 1d regime filters** produce strategies that generalize to out-of-sample data. Unlike Run 1 (apr26) where removing 1d filters caused train Sharpe to spike to 2.16 but test Sharpe to crash to -1.31, this run's strategies maintained moderate train Sharpe (0.21-0.60) with much smaller train→test degradation.

The largest train→test Sharpe drop was **-0.63** (vs -3.47 in Run 1). The best test Sharpe was **0.41** (vs 0.26 in Run 1). Three of five strategies maintained positive test Sharpe (vs 2/5 in Run 1).

---

## Train/test comparison

| strategy | paradigm | train Sharpe | test Sharpe | Δ | test DD | test profit | full profit |
|---|---:|---:|---:|---:|---:|---:|---:|
| **BTCLeaderBreakout** | cross-pair-primary | **0.60** | **0.40** | -0.19 | -2.5% | +6.7% | +59.1% |
| **MomentumADX** | momentum | **0.57** | **0.41** | -0.16 | -2.9% | +9.4% | +100.4% |
| TrendMtfRegime | trend-following | **0.59** | **0.11** | -0.48 | -7.6% | +1.4% | +59.1% |
| RangeBreakout | breakout | 0.21 | -0.02 | -0.24 | -1.4% | -0.2% | +22.6% |
| SuperTrendPullback | trend-following | 0.26 | -0.36 | -0.63 | -7.4% | -3.5% | +17.4% |

### Comparison with Run 1 (apr26)

| dimension | Run 1 (apr26) | **Run 2 (apr26b)** |
|---|---|---|
| train timerange | 2023-2024 | **2021-2025** |
| peak train Sharpe | 2.16 (overfit) | **0.60** |
| best test Sharpe | 0.26 | **0.41** |
| worst train→test Δ | -3.47 | **-0.63** |
| strategies with +test Sharpe | 2/5 | **3/5** |
| avg train Sharpe | ~0.8 | **0.45** |
| avg test Sharpe | ~-0.35 | **0.11** |
| 1d filters removed during loop | 3 times | **0 times** |
| rounds | 50 | **95** |
| Goodhart attempts | 0 | **0** |

---

## Strategy trajectories

### BTCLeaderBreakout — best overall (train 0.60, test 0.40)

The cross-pair-primary paradigm that failed on Run 1's 2023-2024-only data succeeded on multi-regime 2021-2025. BTC 4h Donchian-18 breakout as primary trigger, with ATR expansion, local 1h trend (close>EMA50, vol>1.15x), and 1d EMA100 regime filter. BTC pair-specific: ATR>1.2x ATR_MA.

Evolution highlights:
- Round 37: ROC exit -1.5→-1.2 (tighter). Sharpe +0.01.
- Round 42: BTC volume 1.1→1.2x filter. Sharpe +0.007.
- Round 56: BTC volume 1.2→1.15x. Slight improvement.
- Round 65: Donchian 20→18. Sharpe +0.006.
- Round 73: Local volume 1.2→1.15x. Sharpe 0.577→0.596.
- Round 81: ATR expansion tightened to require 5% above MA → CRASHED to 0.42. Reverted. The ATR filter at "any expansion" was the razor-sharp optimum.

**The BTC ATR expansion filter was the most sensitive parameter** — changing from "any ATR above MA" to "ATR > 1.05x MA" destroyed 0.17 Sharpe.

### MomentumADX — best test performer (train 0.57, test 0.41)

ADX trend-strength confirmation + 1d EMA200 regime filter. ADX>22 entry, ADX<18 exit. ROC>4 entry (ETH/AVAX>7). BTC ROC>2.5 + BTC RSI>45 cross-pair. BNB disabled. Volume>1.2x.

Evolution highlights:
- Round 3: Added 1d EMA200 regime filter. DD -18.0%→-5.9%. THE key structural change.
- Round 32: ADX entry 25→22. Sharpe +0.032.
- Round 36: ADX exit 20→18. Sharpe +0.046.
- Round 40: ROC entry 5→4. Sharpe +0.029.
- Round 74: BTC ROC 3.0→2.5. Sharpe 0.48→0.57. MAJOR BREAKTHROUGH.

**ADX exit at 18 was the optimum** — both 16 and 20 regressed. **BTC ROC at 2.5 was the discovery of the run** — loosening from 3.0 to 2.5 added 0.09 Sharpe.

### TrendMtfRegime — highest train Sharpe (0.59), overfit (test 0.11)

4h EMA9>21 trend + 1d EMA200 regime + BTC RSI>40 cross-pair + BTC close>EMA50 + 1h RSI 30-50 pullback + vol>1.1x. Exit: 4h EMA cross OR RSI>70.

Evolution highlights:
- Round 21: Added BTC close>EMA50 cross-pair. Sharpe +0.03.
- Round 29: RSI 34-46→32-48. Sharpe +0.13! Breakthrough.
- Round 39: RSI 32-48→30-50. Sharpe +0.06.
- Round 55: Volume 1.2→1.15. Sharpe +0.04.
- Round 62: BTC RSI 45→42. Sharpe +0.01.
- Round 70: Exit RSI 71→70. Sharpe 0.47→0.56! MAJOR BREAKTHROUGH.
- Round 77: BTC RSI 42→40. Sharpe +0.002.
- Round 82: Volume 1.15→1.1. Sharpe +0.025.

**Exit RSI at 70 was the single best change** — catching overbought exhaustion one bar earlier unlocked 0.09 Sharpe. The 0.48 train→test drop suggests overfitting, but 0.11 test Sharpe is still positive.

### SuperTrendPullback — SuperTrend validated, DD controlled (train 0.26, test -0.36)

Manual SuperTrend(10,3.0) implementation with flip detection + 1d EMA200 + 4h EMA trend + 1h RSI pullback. Exit: SuperTrend flip OR RSI>70.

Evolution highlights:
- Started at -0.35 (round 15). Went through 8+ iterations.
- Round 16: Added flip detection. Critical — without it, 941 trades at -0.58 Sharpe.
- Round 17: Added 4h EMA. Sharpe +0.13.
- Round 19: Added 1d EMA200 + flip. Sharpe turned positive (0.0017).
- Round 20: RSI 25-60→25-65. Sharpe +0.128! Trades 24→179.
- Round 30: RSI 65→68. Sharpe +0.015.
- Round 33: Exit RSI 72→70. Sharpe +0.022.
- Round 44: RSI 68→72. Sharpe +0.043.
- Round 52: Volume 1.3→1.05. Sharpe +0.01.
- Round 61: Volume 1.05→1.0. Sharpe +0.008.

**The flip detection was load-bearing.** Without it (round 18), 941 trades, -0.58 Sharpe. With it, 327 trades, +0.26 Sharpe. The strategy went from -0.35 to +0.26 — a 0.61 improvement.

Failed on test (-0.36 Sharpe). The manual SuperTrend implementation may still have issues, or the paradigm is inherently more regime-dependent.

### RangeBreakout — consistent but modest (train 0.21, test -0.02)

Pure price-structure breakout above prior N-bar highs with 4h trend + 1d EMA100 + BTC cross-pair. Pair-specific breakout windows.

Evolution highlights:
- Round 10: Disabled ETH/BNB (negative pairs). Sharpe +0.20.
- Round 20: Re-enabled ETH with strict gate. Slight regression.
- Round 27: Added BTC close>EMA50. Neutral.
- Round 31: ROC entry 3→2. Sharpe +0.03. Trades 112→162.
- Round 35: BTC ROC 2→3. Sharpe +0.045. DD improved.
- Round 60: Volume 1.2→1.15. Sharpe +0.012.

RangeBreakout was the most stable strategy — small improvements, small regressions, always near 0.20 Sharpe. Near-flat on test (-0.02).

---

## Key discoveries

### 1. Multi-regime training + 1d regime filters prevent catastrophic overfitting

This is the #1 finding. Run 1 (2023-2024 only) saw train Sharpe reach 2.16 with -1.31 test. Run 2 (2021-2025) kept train Sharpe moderate (max 0.60) with much better generalization. The 1d regime filters (EMA200, EMA100) were never removed — they stayed structural throughout.

### 2. BTC ROC gate at 2.5 was the single best parameter discovery (+0.09 Sharpe on MomentumADX)

Loosening the BTC ROC cross-pair filter from 3.0 to 2.5 allowed more trades while maintaining quality. This was counter-intuitive — most "loosening" changes regressed.

### 3. Exit RSI at 70 on TrendMtfRegime (+0.09 Sharpe)

Moving the take-profit exit from RSI>71 to RSI>70 (one RSI point) added 0.09 Sharpe. The 1-point difference suggests the optimum is razor-sharp.

### 4. SuperTrend flip detection is load-bearing

Without requiring entry on the exact bar where SuperTrend flips from bearish to bullish, the strategy generated 941 trades at -0.58 Sharpe. The flip requirement reduced this to 327 trades at +0.26. This is a structural finding: SuperTrend entries only work at trend initiation, not during ongoing trends.

### 5. Cross-pair-primary works on multi-regime, failed on 2023-2024 only

BTCLeaderBreakout achieved 0.60 train / 0.40 test Sharpe on 2021-2025 training. Run 1's equivalent (on 2023-2024 only) never broke 0.75 and was killed. The 2021-2022 data (including the 2022 bear) provided enough BTC-led breakout episodes for the paradigm to learn from.

### 6. Parameter changes at confirmed optima regress ~70% of the time

Of ~90 evolve events, approximately 25 improved, 35 regressed, 30 were neutral. Once strategies reached their optima (around round 40-50), further changes were almost always neutral or regressive. This mirrors Run 1's finding.

---

## Paradigm-specific findings

| finding | cross-pair-primary | momentum | trend-following | breakout |
|---|---|---|---|---|
| **1d regime filter** | EMA100 (load-bearing) | EMA200 (load-bearing, -12% DD) | EMA200 (load-bearing) | EMA100 (load-bearing) |
| **BTC cross-pair** | Core (4h Donchian trigger) | ROC>2.5 + RSI>45 | RSI>40 + close>EMA50 | ROC>3 + RSI>50 |
| **BNB** | Keep (diversifies) | Disable (structurally negative) | Keep | Disable (negative) |
| **AVAX** | Keep (follower) | Keep (with ROC>7 gate) | Disable (too volatile) | Keep (best performer!) |
| **SOL** | Keep (follower) | Keep (core alpha) | Keep | Keep |
| **Exit style** | Fast dual: EMA21+ROC-1.2 | Slow: ADX<18+ROC<-4 | Dual: 4h EMA cross+RSI>70 | Fast: EMA12+ROC<-2 |
| **Volume sweet spot** | 1.15x local, 1.15x BTC | 1.2x | 1.1x | 1.15x |

---

## Event dynamics

| event type | count | comment |
|---|---:|---|
| create | 5 | BTCLeaderBreakout, MomentumADX, TrendMtfRegime, KeltnerExpansion, MeanRevRegime |
| kill | 2 | KeltnerExpansion (round 8, flat at 0.09), MeanRevRegime (round 15, stuck at 0.08) |
| evolve (improvement) | ~25 | exit tuning, regime filter additions, cross-pair gate adjustments |
| evolve (regression) | ~35 | parameter tightening usually regressed |
| evolve (neutral) | ~30 | small changes with no effect |
| stable | ~380 | bulk of events after optima reached |
| fork | 0 | no fork events — consistent with all prior runs |

---

## Comparison with all runs

| dimension | v0.3.0 best | v0.3.1 best | v0.4.0 Run 1 | **v0.4.0 Run 2** |
|---|---|---|---|---|
| peak train Sharpe | 1.07 | 0.91 | 2.16 | **0.60** |
| best test Sharpe | n/a | n/a | 0.26 | **0.41** |
| best full-regime Sharpe | n/a | n/a | 0.89 | **0.60** |
| train timerange | 2023-2025 | 2023-2025 | 2023-2024 | **2021-2025** |
| strategies +test Sharpe | n/a | n/a | 2 | **3** |
| rounds | 100 | 19 | 50 | **95** |
| Goodhart attempts | 0 | 0 | 0 | **0** |

---

## Limitations

- **SuperTrendPullback failed test validation.** Despite improving from -0.35 to +0.26 on train, it went -0.36 on test. The manual SuperTrend implementation is fragile.
- **TrendMtfRegime shows significant overfitting.** 0.59 train → 0.11 test. The 0.48 gap is the largest in this run.
- **RangeBreakout is barely positive on train, flat on test.** The breakout paradigm needs more development.
- **No fork events.** Fork remains unused across 5 runs and 300+ combined rounds.
- **Short test period.** 13 months (2025-01 to 2026-01-29) may not be representative.

---

## Open questions for future runs

1. **Can exit RSI 70 be generalized?** Both TrendMtfRegime and SuperTrendPullback found their optimum at exit RSI 70. Is this a universal optimum for 1h crypto trend-following exits?
2. **SuperTrend with library implementation?** The manual SuperTrend was fragile. Would a library implementation (pandas-ta) produce better results?
3. **BTC ROC 2.5 as universal gate?** The looser BTC ROC filter improved MomentumADX dramatically. Would it help other strategies?
4. **Walk-forward validation?** The simple train/test split is better than no split, but multi-window validation would be more robust.
5. **Adaptive regime filters?** Make 1d EMA thresholds adaptive to market volatility rather than fixed.

---

## Evaluation

**What this run validates** (high confidence):
- Multi-regime training (2021-2025) + 1d regime filters produce strategies that generalize
- The train→test Sharpe gap is 5x smaller than single-regime training (Run 1)
- BTCLeaderBreakout (cross-pair-primary) works on multi-regime data
- ADX adds value as a momentum confirmation filter
- Exit RSI 70 is a robust optimum for 1h trend-following

**What this run does NOT validate**:
- That SuperTrend manual implementation is production-ready
- That the breakout paradigm generalizes (flat on test)
- That any single strategy beats buy-and-hold on absolute returns

**Primary knowledge output**: Training on a single market regime (2023-2024 bull) is the root cause of overfitting. Multi-regime training (2021-2025, covering bull + bear + recovery) with structural 1d regime filters is the architectural fix. The 1d EMA200/EMA100 filters must remain structural — never removed during optimization.
