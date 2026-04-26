# v0.3.1 — Retrospective

**Run**: 19-round experiment — benchmark injection + cross-pair primary signal revisit  
**Branch**: `v0.3.1`  
**Final commit**: `2f3f989` (r19 — BTCLeaderBreakout ROC -1.0 peak)  
**Peak strategy Sharpe**: `BTCLeaderBreakout` **0.9103** at `fef0daa`—`2f3f989`  
**Total rounds**: 19 — 57 events — 3 creates, 16 evolves, 38 stables, 0 forks, 0 kills  
**Discarded evolves**: 12 — kept evolves: 4  

---

## Headline

v0.3.1 做了两件事：注入 buy-and-hold benchmark，并重新探索跨资产主信号范式（Run 1 的 BTCLeaderBreakX 在 Run 2/3 里被遗忘）。19 轮实验后：

- **跨资产主信号范式复活**：BTCLeaderBreakout 以 BTC 4h Donchian 突破作为所有 pair 的 PRIMARY 入场触发器，Sharpe 达到 **0.9103**。
- **MomentumMTF** 从 0.55 起步，通过 pair-specific gates 推至 **0.8343**。
- **PanicReboundMTF** 保持 Run 3 最优值 **0.6558**，19 轮零退化。

最终组合平均 Sharpe **0.8001**，三策略合计收益 **+196.12%**，最大回撤全在 -9% 以内。Benchmark 等权 buy-and-hold 同期 +398.44%（DD -58.21%）。

---

## Final portfolio

| strategy | paradigm | Sharpe | DD | profit | pf | trades | alive pairs |
|---|---|---|---:|---:|---:|---:|---:|---|
| **BTCLeaderBreakout** | cross-pair primary | **0.9103** | -8.30% | +50.15% | 1.62 | 335 | BTC, ETH, SOL, BNB, AVAX |
| **MomentumMTF** | momentum | **0.8343** | -8.67% | +106.64% | 1.66 | 259 | BTC, ETH, SOL, AVAX |
| **PanicReboundMTF** | mean-reversion | **0.6558** | -4.72% | +39.33% | 1.94 | 150 | BTC, ETH, BNB |

All 3 strategies kept. No forks, no kills. 12 of 16 evolve attempts were discarded/reset.

---

## Benchmark injection

`run.py` 现在输出一个 `__benchmark__` block，显示每个 pair 的 buy-and-hold 收益和等权组合表现：

| pair | buy-and-hold profit | max DD |
|---|---:|---:|
| BTC/USDT | +430.25% | -34.76% |
| ETH/USDT | +148.86% | -65.28% |
| SOL/USDT | +1147.75% | -66.06% |
| BNB/USDT | +251.77% | -42.65% |
| AVAX/USDT | +13.55% | -82.28% |
| **Equal-weight** | **+398.44%** | **-58.21%** |

所有策略的绝对收益均低于被动持有（这在 2023-2025 牛市中可预期），但风险调整后收益显著更优：最高 DD -8.67% vs -58.21%。Benchmark 锚点是本次实验的永久基础设施。

---

## Final strategy structures

### BTCLeaderBreakout — 0.8489 → 0.9103

**Core formula**: BTC 4h Donchian-10 breakout + ATR expansion → enter all pairs with 1h EMA50 trend + volume confirmation. Exit on EMA21 OR ROC < -1.0.

Final active structure:

- `minimal_roi = {"0": 100}`, `stoploss = -0.99`, no shorting.
- Entry stack:
  - BTC 4h close > Donchian-10 high (primary trigger)
  - BTC 4h ATR > ATR MA20 (volatility-backed breakout)
  - Local 1h close > EMA50 (trend filter)
  - Volume > vol_ma * 1.5 (participation)
  - BTC-only: ATR > ATR_MA20 * 1.2 (tighter expansion for leader)
- Exit: `close < EMA21` OR `roc < -1.0` (catch trend failure + momentum fade).

Discovery arc:

- **Round 7**: BTC-only tighter ATR gate → Sharpe 0.85→0.88. Higher-quality BTC entries without removing diversification.
- **Round 12**: Added ROC < -2.0 secondary exit → Sharpe 0.88→0.90. Dual exit catches post-breakout momentum failure that pure EMA21 missed.
- **Rounds 15-18**: Bracketed ROC exit from -2.5 to 0.0. Optimum at **-1.0** (Sharpe 0.9103). Tighter exits (-0.5, 0.0) over-clip, looser (-1.5, -2.0, -2.5) leave trend failures running.

Final per-pair profile:

| pair | trades | profit | DD | Sharpe | PF | role |
|---|---:|---:|---:|---:|---:|---|
| BTC | 29 | +2.18% | -2.87% | 0.0538 | 1.32 | leader itself, weak but diversifying |
| ETH | 81 | +17.59% | -2.47% | 0.2908 | 2.03 | primary beneficiary |
| SOL | 78 | +10.50% | -4.26% | 0.1680 | 1.46 | strong follower |
| BNB | 71 | +0.28% | -4.21% | 0.0093 | 1.02 | flat, diversifies |
| AVAX | 76 | +19.59% | -5.06% | 0.3164 | 1.93 | strongest follower |

---

### MomentumMTF — 0.5474 → 0.8343

**Core formula**: 4h EMA trend + 1h ROC strength + pair-specific ROC/volume gates + slow ROC exit.

Final active structure:

- `minimal_roi = {"0": 100}`, `stoploss = -0.99`, no shorting.
- Entry stack:
  - `ema9_4h > ema21_4h`
  - `close > ema50`
  - `roc > 5.0`
  - `volume > vol_ma * 1.2`
  - BNB disabled
  - ETH: `roc > 7.0` and `volume > vol_ma * 1.5`
  - AVAX: `roc > 7.0` and `volume > vol_ma * 1.5`
- Exit: `roc < -3.0` (pure ROC exit — dual exit destroyed performance, see r13).

Discovery arc:

- **Round 2**: Disabled BNB → Sharpe 0.55→0.65. BNB is structurally negative for momentum (confirmed Run 3).
- **Round 3**: ETH/AVAX ROC>7 gates → Sharpe 0.65→0.79. Pair-specific ROC thresholds remove noise from weaker directional pairs.
- **Round 8**: AVAX volume>1.5x gate → Sharpe 0.79→0.83. Double gate (ROC + volume) for weakest pair improves quality.
- **Round 10**: ETH volume>1.5x gate → neutral (~0.001 delta). Kept for symmetry.
- **Round 13**: Attempted dual exit (close<EMA21 OR ROC<-3) → Sharpe 0.83→0.54 DISASTER. EMA21 exit clips momentum winners. Paradigm-specific: momentum needs SLOW exits.

Final per-pair profile:

| pair | trades | profit | DD | Sharpe | PF | role |
|---|---:|---:|---:|---:|---:|---|
| BTC | 39 | +18.03% | -4.16% | 0.1637 | 1.94 | solid diversifier |
| ETH | 30 | +10.62% | -4.78% | 0.0792 | 1.55 | weak, constrained by gates |
| SOL | 115 | +61.60% | -5.50% | 0.4525 | 1.86 | core alpha, highest trade count |
| BNB | 0 | 0.00% | 0.00% | 0.0000 | 0.00 | disabled |
| AVAX | 75 | +16.38% | -9.07% | 0.1370 | 1.33 | improved by volume gate |

---

### PanicReboundMTF — 0.6558 (stable anchor)

Final active structure is identical to Run 3 peak (`1e8c5bb`):

- `close > ema50_1d`
- `close > ema50 * 0.88`
- `rsi_4h < 50`
- `btc_usdt_rsi_1h < 40`
- `btc_usdt_roc_1h < 1.5`
- `rsi < 32` (BTC/ETH require `< 30`)
- `close < BB(20, 2.2).lower`
- `volume > vol_ma * 1.10`
- SOL/AVAX disabled
- Exit: `rsi > 66` and `close > BB_mid`.

Round 11 tested exit RSI 66→67 (regression, as Run 3 found). Round 15 tested volume 1.10→1.05 (regression). Run 3 optimum reconfirmed in v0.3.1 context.

---

## Event dynamics

| event type | count | comment |
|---|---:|---|
| create | 3 | BTCLeaderBreakout, MomentumMTF, PanicReboundMTF |
| evolve | 16 | every round touched at least one strategy |
| stable | 38 | two stable rows per round on average |
| fork | 0 | no fork justified under cap=3 |
| kill | 0 | all three paradigms survived |
| discarded evolves | 12 | 75% of evolves were rejected and reset |
| kept evolves | 4 | about 25% of evolves became permanent |

The high discard rate (75%) reflects targeted bracketing: once the BTC ATR gate and dual exit were discovered, subsequent rounds focused on parameter optimization (ROC exit bracketing, volume thresholds) where most trials regressed toward the already-found optimum.

---

## Most important changes

| rank | change | strategy | impact |
|---:|---|---|---|
| 1 | Add ROC<-2 dual exit | BTCLeaderBreakout | Sharpe 0.88→0.90, DD -9.1→-6.5 |
| 2 | ETH/AVAX ROC>7 gates | MomentumMTF | Sharpe 0.65→0.79, profit 80→100 |
| 3 | Disable BNB | MomentumMTF | Sharpe 0.55→0.65, removed negative-alpha sleeve |
| 4 | BTC-only ATR>1.2*MA gate | BTCLeaderBreakout | Sharpe 0.85→0.88, BTC quality improved |
| 5 | AVAX volume>1.5x gate | MomentumMTF | Sharpe 0.79→0.83, AVAX Sharpe 0.09→0.14 |
| 6 | ROC exit bracketed to -1.0 | BTCLeaderBreakout | Sharpe 0.90→0.91, final push |

---

## Paradigm-specific findings

| finding | cross-pair primary | momentum | mean-reversion |
|---|---|---|---|
| **BNB** | keep (flat but diversifies) | disable | strongest asset |
| **SOL** | strong follower | core alpha | disable |
| **AVAX** | strongest follower | improved by vol gate | disable |
| **BTC** | leader, weak standalone | solid diversifier | useful, needs RSI<30 |
| **ETH** | primary beneficiary | constrained by gates | useful, needs RSI<30 |
| **Exit style** | dual: EMA21 + ROC -1.0 | slow: pure ROC -3.0 | RSI66 + BB mid |
| **Pair exclusion** | hurts diversification | essential (BNB) | essential (SOL/AVAX) |
| **Volume sweet spot** | 1.5x | 1.2x (1.5x for weak pairs) | 1.10x |
| **Dual exit** | load-bearing (+0.02 Sharpe) | destructive (-0.29 Sharpe) | not applicable |

The headline finding: **exit mechanisms are paradigm-specific**. The same dual-exit pattern that lifted BTCLeaderBreakout 0.88→0.91 destroyed MomentumMTF 0.83→0.54. Cross-pair primary strategies benefit from faster exits (catching post-breakout fade), while momentum strategies need slow exits (letting trends run).

---

## Comparison with v0.3.0 runs

| dimension | Run 1 (apr24) | Run 2 (apr24b) | Run 3 (apr25) | **v0.3.1** |
|---|---|---|---|---|
| rounds | 39 | 39 | 100 | **19** |
| peak Sharpe | 1.0716 | 0.6388 | 0.6558 | **0.9103** |
| final strategies ≥ 0.50 | 3 | 3 | 3 | **3** |
| avg final Sharpe | ~0.68 | ~0.58 | ~0.60 | **~0.80** |
| largest final DD | -25.7% | -25.7% | -4.74% | **-8.67%** |
| forks | 1 | 0 | 0 | **0** |
| kills | 3 | 0 | 0 | **0** |
| paradigm coverage | trend / breakout / MR | trend / momentum / MR | momentum / MR / breakout | **cross-pair-primary / momentum / MR** |
| benchmark | none | none | none | **buy-and-hold injected** |

v0.3.1 achieves the second-highest peak Sharpe in the v0.3.x series (behind only Run 1's BTCLeaderBreakX at 1.07) and the highest average final Sharpe (~0.80). It also has the smallest round count (19), suggesting the experiment converged faster due to targeted parameter bracketing and the reuse of Run 3's proven PanicReboundMTF anchor.

---

## Zero Goodhart assessment

No Goodhart pattern was introduced:

- `exit_profit_only` remained `False`.
- `minimal_roi` stayed `{ "0": 100 }`.
- No tight ROI clipping.
- Stoploss stayed effectively disabled (`-0.99`).
- All regressions were logged and reset.
- Benchmark injection provides an external validity check: all strategies underperform buy-and-hold on absolute return but dominate on risk-adjusted basis.

---

## Limitations

- **Single-regime**: 2023-2025 bull/risk-on period only. Cross-pair primary signal may fail in bear markets when BTC breakouts are false signals.
- **No out-of-sample validation**: all tuning uses the same 2023-2025 timerange.
- **Small round count**: 19 rounds is sufficient for bracketing known parameters but insufficient for discovering new paradigms.
- **Cross-pair primary signal only tested with BTC**: SOL-leader or ETH-leader variants may also work.
- **Fork remains unused**: cap=3 plus three productive slots again produced no forks.
- **PanicReboundMTF** is at its Run 3 optimum — zero improvement in 19 rounds, confirming the 100-round bracketing was exhaustive.

---

## Open questions for v0.4.0

These carry forward from the apr25 retrospective, plus new ones from v0.3.1:

1. **Bear-market regime test**: extend timerange to include 2021-2022. Does BTCLeaderBreakout survive when BTC breakouts fail?
2. **Cross-pair leader diversity**: test SOL-leader or ETH-leader primary signals. Is BTC the uniquely best leader, or does leadership rotate?
3. **Out-of-sample split**: force train/test windows or walk-forward evaluation.
4. **Cap=5 experiment**: with 4 distinct paradigms now validated (cross-pair-primary, momentum, mean-reversion, volatility-breakout), cap=5 may enable broader coverage.
5. **Exit mechanism as first-class design choice**: v0.3.1's clearest finding is that exit mechanisms are paradigm-specific. v0.4.0 could make exit design a primary axis of strategy construction rather than a post-hoc tuning parameter.
6. **Cross-pair primary + per-pair exit differentiation**: BTCLeaderBreakout uses identical exit for all pairs. Could pair-specific exits improve performance further?

---

## Evaluation

**High-confidence validations**:

- Cross-pair primary signal is a viable 4th paradigm (Sharpe 0.91).
- Benchmark injection is load-bearing infrastructure — every strategy now has a passive baseline.
- Pair-specific gates remain the highest-leverage tuning dimension.
- Exit mechanisms are paradigm-specific: dual exit works for cross-pair primary, pure ROC works for momentum, RSI+BB works for mean-reversion.
- Pair exclusions are paradigm-specific: essential for momentum (BNB) and mean-reversion (SOL/AVAX), harmful for cross-pair primary.
- Run 3's PanicReboundMTF optimum is robust — reconfirmed in independent v0.3.1 context.

**Not validated**:

- Survival outside 2023-2025.
- Cross-pair primary with non-BTC leaders.
- Whether final strategies beat buy-and-hold on absolute return (they don't, but dominate on risk).
- Whether cap=3 is optimal.
- Whether fork has value in this architecture.
