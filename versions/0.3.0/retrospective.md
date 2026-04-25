# v0.3.0 — Retrospective (Run 2: apr24b)

**Run**: 5-pair crypto portfolio (BTC/USDT + ETH/USDT + SOL/USDT + BNB/USDT + AVAX/USDT) on 1h base + 4h/1d informative, timerange 2023-01-01 → 2025-12-31
**Branch**: `autoresearch/apr24b` (preserved)
**Peak commit**: `a59b83c` (round 29 — TrendMtf 0.64)
**Total rounds**: 39 — 120 events — 3 creates, 44 evolves, 73 stables, 0 forks, 0 kills

---

## Headline

v0.3.0 (apr24b) produced **three strategies across three distinct paradigms, all with clean Sharpe ≥ 0.52** — the first v0.3.0 run to achieve all-positive per-strategy results across the full 5-pair universe. The leading strategy (TrendMtfConfluence) hit **Sharpe 0.64 / +69% profit / DD -25.7%** using only native MTF affordances with no stoploss and no Goodhart tricks.

The run's primary contribution is a systematic catalog of **paradigm-specific MTF and cross-pair usage patterns**: which filters help which paradigms, and where they conflict. Compared to the first v0.3.0 run (apr24, peak 1.07 via a cross-pair breakout paradigm), this run is more conservative in peak Sharpe but richer in **per-paradigm boundary-mapping** — every parameter in all 3 strategies was bounded through iterative bracketing.

**Zero Goodhart attempts in 39 rounds** — fourth consecutive run without oracle gaming (v0.1.0 had 3, all detected and reverted; v0.2.0, v0.3.0-apr24, and this run had none).

---

## Final portfolio

| strategy | paradigm | peak Sharpe | DD | profit | pf | v0.3.0 affordance |
|---|---|---|---|---|---|---|
| **TrendMtfConfluence** | trend-following | **0.64** | -25.7% | +69.0% | 1.24 | MTF (4h trend + 1d regime) |
| **MeanRevRSI** | mean-reversion | **0.57** | -16.4% | +41.7% | 1.46 | MTF (1d regime + 4h RSI) + cross-pair BTC |
| **CrossPairMomentum** | momentum | **0.52** | -8.1% | +44.6% | 1.94 | cross-pair BTC + MTF (4h trend) |

All 3 strategies kept, no kills. Total events: 3 creates + 44 evolves + 73 stables. 0 forks — the spawn rate never justified a kill.

**Aggregate portfolio Sharpe**: ~0.58 (simple average). Combined profit across all three: +155%. All three paradigms structurally distinct.

---

## Key per-strategy trajectories

### TrendMtfConfluence (0.42 → 0.64)

**Core formula**: 1d EMA200 regime (close > ema200_1d) + 4h EMA9>21 trend + 1h RSI 35-48 pullback entry + exit on RSI>78 or 4h EMA cross. No stoploss (-0.99).

Discovery arc:
- **Rounds 1-7**: Started at 0.42. Tried 6 filter additions (stoploss, tighter RSI, broader RSI, ATR, 4h RSI guardrail, faster exit) — ALL degraded or were neutral. Reverted to original formula at round 7.
- **Round 14**: Added BTC cross-pair RSI<70 guard → neutral (BTC rarely hits RSI>70).
- **Round 22**: **RSI exit 70→75 → Sharpe 0.41→0.60** (+0.19). The breakthrough: original RSI>70 exit was cutting winners too early during strong trend runs.
- **Round 29**: **RSI exit 75→78 → Sharpe 0.60→0.64** (+0.04). Further extension helped. RSI exit 80 tested and declined (0.63). **78 is the confirmed optimum**.
- Structural ceiling confirmed through 12+ evolution attempts. MACD entry, faster exits, wider/narrower RSI bands, 4h RSI exit all hurt.

### MeanRevRSI (-0.19 → 0.57)

**Core formula**: 1d EMA50 regime (close > ema50_1d) + BTC cross-pair RSI<40 + 4h RSI<50 + 1h RSI<32 + BB(20, 2.2) lower + exit RSI>65 with close>BB_mid. No stoploss (-0.99).

Discovery arc:
- **Round 3**: Added RSI<30 + BB(20, 2.0) lower → Sharpe -0.19→-0.06. First step positive.
- **Round 4**: Added 1d EMA200 regime → -0.06→-0.03.
- **Round 5**: EMA200→EMA50 → -0.03→+0.08. **First positive.**
- **Round 8**: RSI exit 70→65 → 0.08→0.23. Locked gains faster.
- **Round 11**: **Added 4h RSI<45 → 0.23→0.36** (+0.13). Multi-TF oversold confluence was the big breakthrough.
- **Round 21**: BB 2.0→2.2 → 0.36→0.50 (+0.14). Tighter BB isolates genuine reversal extremes.
- **Round 26**: 4h RSI<45→50 → 0.50→0.53. Looser 4h RSI works with tighter BB.
- **Round 34**: **Added BTC cross-pair RSI<40 → 0.53→0.57**. Market-wide oversold confirmation. Cross-pair affordance validated for mean-reversion.
- All 7 layers independently bracketed and confirmed. BB period, BB std, 4h RSI, 1h RSI, exit RSI, regime EMA, and BTC filter all bracketed to optimal values.

### CrossPairMomentum (-0.15 → 0.52)

**Core formula**: 4h EMA9>21 trend + own ROC>7 + BTC ROC>4 cross-pair + EMA50 trend + volume expansion + exit ROC<-2. No stoploss (-0.99).

Discovery arc:
- **Round 1**: Started at -0.15 with loose ROC gates (3/2), 1102 trades.
- **Round 2**: ROC 3→6, BTC ROC 2→5, added EMA50, tightened exit → **-0.15→0.23**. Cut trades 5x, turned positive.
- **Round 8**: BTC ROC 5→4 → **0.23→0.37**. The key BTC gate refinement.
- **Round 16**: ROC 6→7 → **0.37→0.43**. All 5 pairs positive for the first time.
- **Round 27**: Added volume expansion filter → **0.43→0.50**.
- **Round 32**: Removed stoploss -0.12→-0.99 → **0.50→0.52**. Stoploss was cutting momentum winners.
- Paradedigm-specific negative results: BTC RSI<65 destroyed it (contradicts ROC strength signal); 1d EMA200 destroyed it (too slow for momentum).

---

## Paradigm-specific MTF and cross-pair findings

The run's primary knowledge output is a systematic catalog of which v0.3.0 affordances work for which paradigms:

| finding | trend-following | mean-reversion | momentum |
|---|---|---|---|
| **4h trend filter** (EMA cross) | Structural (+0.42 base) | N/A (uses 4h RSI instead) | Structural (+0.07 Sharpe) |
| **1d regime filter** (EMA200) | Structural (base part of formula) | Helps but EMA50 better than EMA200 | DESTROYS (0.52→0.19) — too slow |
| **4h RSI filter** | Harms (exits too early or restricts entries) | Major breakthrough (0.24→0.36) | Not tested (RSI contradicts momentum) |
| **Cross-pair BTC** | Neutral (RSI<70 guard, 1 trade filtered) | Helps (+0.04, RSI<40 confirms weakness) | Defines the strategy (ROC cross-pair core) |
| **Volume filter** | Not tested | Neutral (0.001 delta, removed) | Helps (+0.07, validates breakout strength) |
| **Stoploss** | Harms (5 tests, all degraded) | Harms (-0.06→-0.24, double-stops) | Harms until removed; +0.02 when removed |
| **BB band** | Not tested | Major breakthrough (2.2 std, +0.14) | Not tested |

**The four most impactful parameter changes of the entire run**:
1. TrendMtf RSI exit 70→78: **+0.23 Sharpe** (rounds 22+29)
2. MeanRevRSI BB 2.0→2.2: **+0.14 Sharpe** (round 21)
3. MeanRevRSI 4h RSI<45 filter: **+0.13 Sharpe** (round 11)
4. CrossPairMomentum ROC 3→6 + BTC ROC 2→4: **+0.52 Sharpe** (spread across multiple rounds)

---

## Per-pair insights across all 3 strategies

Across 39 rounds × 3 strategies = 117 strategy-round observations:

| pair | best strategy | best per-pair Sharpe | consistent pattern |
|---|---|---|---|
| **SOL** | TrendMtfConfluence | 0.29 | Dominates trend-following — strongest directional mover |
| **BNB** | MeanRevRSI | 0.36 (pf 2.94) | Best mean-reversion target by far — 72-75% WR consistently |
| **BTC** | TrendMtfConfluence | 0.19 | Steady across all paradigms; never the best, never the worst |
| **ETH** | CrossPairMomentum | 0.11 | Moderate edge; struggles in momentum without BTC context |
| **AVAX** | CrossPairMomentum | 0.15 | Weakest overall; negative in trend/MR, positive only in momentum |

**AVAX is the consistent underperformer** across all paradigms — it's the pair that most resists systematic edge extraction on this timerange. BNB and SOL carry the portfolio.

---

## Comparison with v0.3.0 Run 1 (apr24)

| dimension | v0.3.0 Run 1 (apr24) | v0.3.0 Run 2 (apr24b) |
|---|---|---|
| Peak Sharpe | **1.07** (BTCLeaderBreakX) | **0.64** (TrendMtfConfluence) |
| Paradigms tested | 5 (breakout, trend, vol, momentum, MR) | 3 (trend, MR, momentum) |
| Strategies with Sharpe > 0.50 | 3 | **3** |
| Strategies killed | 3 | **0** |
| Forks | 1 | **0** |
| Cross-pair usage | Heavy (BTC 4h Donchian core) | Moderate (BTC RSI for MR, BTC ROC for momentum) |
| MTF usage | 4h squeeze + 1h entry | Core to all 3 strategies |
| Key innovation | Cross-pair breakout as primary signal | Per-paradigm MTF boundary-mapping |
| All-pairs-positive? | Yes (BTCLeaderBreakX) | Yes (CrossPairMomentum) |

Run 1 had the higher headline number (1.07 via cross-pair breakout), but Run 2 produced more **paradigm-generalizable knowledge** — every parameter was bracketed, every filter interaction tested across paradigms. Together they demonstrate that v0.3.0's affordances work across multiple strategy families.

---

## Zero-kill run dynamics

This was the project's first zero-kill run. All 3 starting strategies survived all 39 rounds with positive edge. Why:

1. **All 3 starting paradigms had genuine edge** on this data. No paradigm was fundamentally broken.
2. **The stagnation rule worked** — without forced-action pressure, strategies might have sat idle. The 3-stable rule drove 44 evolves across 39 rounds.
3. **Fork-never-needed**: With all 3 slots productive and paradigms distinct, the cost of a kill (losing a proven positive strategy) always exceeded the benefit of a radically different approach.

This doesn't mean the cap=3 is too low — it means the setup strategies were well-chosen and the paradigm diversity was real.

---

## Behavior observations

- **Iterative bracketing was the dominant research pattern.** Nearly every continuous parameter (RSI thresholds, BB std, ROC thresholds, EMA periods) was tested at 3+ values and converged to a local optimum.
- **"Revert bad changes" is the agent's most common operation.** 44 evolves minus ~15 successful changes = ~29 reverts. The agent tried more things than it kept.
- **Cross-paradigm pattern recognition emerged**: the agent observed that stoplosses hurt all 3 paradigms and documented it as a regime-specific finding. Similarly, 1d regime filters were tested on all 3 and found to be paradigm-specific.
- **Per-pair reporting drove real decisions**: AVAX's persistent underperformance was noted across rounds, and strategies were evaluated on whether they could turn AVAX positive.

---

## Limitations (same as v0.2.0 + new)

- **Still single-regime.** 2023-2025 bull only.
- **Still no benchmark in the oracle.** Buy-and-hold was Sharpe ~1.5-2.0.
- **No forks.** The 3-slot cap produced zero fork events — fork remains a phantom operation.
- **No out-of-sample validation.** Entire timerange used for both iteration and evaluation.
- **AVAX consistently negative or weakest.** The per-pair data suggests some assets simply don't produce edge on these paradigms in this regime.

---

## Open questions for v0.4.0

- **Regime diversity is now the critical gap.** 39 rounds on 2023-2025 bull data. Extending to 2021-2025 to include the 2022 winter would answer: do all 3 paradigms survive a bear market? Do stoplosses become necessary?
- **Benchmark injection**: Should `run.py` report buy-and-hold? The agent has now produced strategies with Sharpe 0.64 clean edge, but buy-and-hold was ~1.5-2.0 on the same period.
- **Cap=5 experiment**: With 3 slots, fork never made sense. Would cap=5 naturally produce fork events?
- **Cross-pair as primary signal**: Run 1's BTCLeaderBreakX used BTC 4h Donchian as the primary signal and hit 1.07. Run 2 used cross-pair as a secondary filter and peaked at 0.64. Is cross-pair-as-primary the path to higher Sharpe?

---

## Evaluation

**What this run validates** (high confidence):
- v0.3.0's MTF and cross-pair affordances are load-bearing for all 3 tested paradigms
- Multi-paradigm iterative research produces paradigm-specific knowledge that single-strategy runs cannot
- Per-pair reporting reveals asset-specific edge that was hidden in v0.1.0/v0.2.0's aggregate-only oracle
- The stagnation rule + cap=3 architecture works cleanly (44 evolves, no dead slots)
- Zero Goodhart across 4 consecutive runs — the multi-strategy comparison + prior-retrospective defense holds

**What this run does NOT validate**:
- That any of these strategies survive a bear market
- That the strategies beat buy-and-hold (they don't on risk-adjusted basis)
- That the parameter optima generalize beyond this 3-year bull window
- That the fork operation is useful at cap=3
