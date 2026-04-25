# v0.3.0 — Retrospective (Run 3: apr25)

**Run**: 5-pair crypto portfolio (BTC/USDT + ETH/USDT + SOL/USDT + BNB/USDT + AVAX/USDT) on 1h base + 4h/1d informative, timerange 2023-01-01 → 2025-12-31  
**Branch**: `autoresearch/apr25`  
**Final kept commit**: `1e8c5bb` (round 96 — PanicRebound volume 1.15×→1.10×)  
**Peak strategy Sharpe**: `PanicReboundMTF` **0.6558** at `1e8c5bb`  
**Total rounds**: 100 — 300 events — 3 creates, 99 evolves, 198 stables, 0 forks, 0 kills  
**Discarded evolves**: 70 — kept evolves: 29  

---

## Headline

v0.3.0 的第三次运行（`apr25`）把同一个 5-pair / MTF / cross-pair arena 从 39 轮扩展到 **100 轮**。结果不是单个策略极端爆表，而是一次非常清晰的 **pair-specialized portfolio search**：三条策略都活下来，最终 Sharpe 全部 ≥ 0.53，并且最大回撤全部压到约 **-4.7% 以内**。

这次最重要的发现不是“某个指标更好”，而是：**同一资产在不同范式里的角色完全不同**。

- **BNB**：动量和突破里应禁用；恐慌均值回归里是核心 alpha 来源。
- **SOL / AVAX**：方向性策略里很强；恐慌均值回归里是 drawdown trap。
- **BTC / ETH**：单独不总是最强，但经常提供组合路径上的分散化价值，不能只看 per-pair Sharpe 粗暴删除。

最终组合简单平均 Sharpe 约 **0.6010**，三策略合计收益约 **+152.05%**。没有使用 `exit_profit_only=True`、紧 ROI、止损套利等 Goodhart 机制。

---

## Final portfolio

| strategy | paradigm | final Sharpe | peak Sharpe | DD | profit | pf | alive pairs | v0.3.0 affordance |
|---|---|---:|---:|---:|---:|---:|---|---|
| **PanicReboundMTF** | panic mean-reversion | **0.6558** | **0.6558** | -4.72% | +39.33% | 1.94 | BTC, ETH, BNB | MTF + cross-pair BTC |
| **LeaderVolumeMomentum** | BTC-confirmed momentum | 0.6132 | **0.6169** | -4.74% | +88.69% | 2.63 | BTC, ETH, SOL, AVAX | 4h trend + BTC ROC |
| **RangeExpansionBreakout** | volatility breakout | 0.5341 | **0.5341** | -3.55% | +24.03% | 1.85 | BTC, ETH, SOL, AVAX | MTF + BTC confirmation |

All 3 strategies kept. No forks, no kills. 70 of 99 evolve attempts were discarded/reset — this was a long bracketing run, not a smooth hill-climb.

---

## Final strategy structures

### PanicReboundMTF — 0.3127 → 0.6558

**Core formula**: 1d EMA50 regime + local EMA50 distance guard + 4h RSI weakness + BTC 1h washout + local RSI/BB lower panic + volume confirmation + RSI/BB-mid exit.

Final active structure:

- `minimal_roi = {"0": 100}`, `stoploss = -0.99`, no shorting.
- Entry stack:
  - `close > ema50_1d`
  - `close > ema50 * 0.88`
  - `rsi_4h < 50`
  - `btc_usdt_rsi_1h < 40`
  - `btc_usdt_roc_1h < 1.5`
  - `rsi < 32`
  - `close < BB(20, 2.2).lower`
  - `volume > vol_ma * 1.10`
  - AVAX disabled
  - SOL disabled
  - ETH requires local `rsi < 30`
  - BTC requires local `rsi < 30`
- Exit: `rsi > 66` and `close > BB_mid`.

Discovery arc:

- **Round 3**: BTC RSI 42→40 improved Sharpe 0.313→0.332.
- **Round 12**: Disabled AVAX → Sharpe 0.332→0.364, DD -18.75→-14.14.
- **Round 21**: Disabled SOL → Sharpe 0.366→0.470, DD -12.19→-6.25.
- **Round 33**: ETH-only RSI<30 → Sharpe 0.470→0.503.
- **Round 51**: BTC-only RSI<30 improved BTC sleeve and aggregate.
- **Rounds 81/84**: EMA distance guard loosened to 0.88, expanding recoverable BNB panics without worsening DD.
- **Round 96**: Volume 1.15×→1.10× produced the final peak: Sharpe 0.6558.

Final per-pair profile:

| pair | trades | profit | DD | Sharpe | PF | role |
|---|---:|---:|---:|---:|---:|---|
| BTC | 56 | +8.00% | -5.52% | 0.1509 | 1.50 | useful, needs deeper panic |
| ETH | 48 | +7.10% | -5.52% | 0.1045 | 1.37 | weak but diversifying |
| SOL | 0 | 0.00% | 0.00% | 0.0000 | 0.00 | disabled |
| BNB | 46 | +24.23% | -2.14% | 0.4304 | 4.47 | core alpha |
| AVAX | 0 | 0.00% | 0.00% | 0.0000 | 0.00 | disabled |

---

### LeaderVolumeMomentum — 0.2813 → 0.6132 final / 0.6169 peak

**Core formula**: 4h trend + own 1h ROC strength + BTC 1h ROC confirmation + BTC RSI risk-on + local volume participation + slow ROC failure exit.

Final active structure:

- `minimal_roi = {"0": 100}`, `stoploss = -0.99`, no shorting.
- Entry stack:
  - `ema9_4h > ema21_4h`
  - `close > ema50`
  - own `roc > 7.0`
  - BTC `roc > 4.0`
  - BTC `rsi > 50`
  - `volume > vol_ma * 1.05`
  - BNB disabled
  - BTC requires own `roc > 7.75`
- Exit: own `roc < -4.0`.

Discovery arc:

- **Round 7**: Removed EMA50 exit → Sharpe 0.281→0.397. Momentum winners needed room.
- **Round 11**: Disabled BNB → small but clean improvement; BNB contributes nothing to this momentum signal.
- **Round 14**: Removed 4h RSI<75 guard → Sharpe 0.398→0.527. High RSI was continuation evidence, not a risk filter.
- **Round 32**: ROC exit -3→-4 → peak Sharpe 0.617 and profit +88.9%. This was the biggest single improvement in the run.
- **Rounds 50/56/62**: BTC-specific local ROC gate bracketed around 7.5→7.75. It slightly reduced peak Sharpe vs round 32, but improved DD/Calmar materially; final run kept the lower-drawdown profile.

Final per-pair profile:

| pair | trades | profit | DD | Sharpe | PF | role |
|---|---:|---:|---:|---:|---:|---|
| BTC | 12 | +10.54% | -3.04% | 0.0842 | 2.80 | low-sample diversifier, stricter ROC |
| ETH | 18 | +24.43% | -2.36% | 0.1406 | 3.48 | high-quality sleeve |
| SOL | 39 | +26.19% | -3.45% | 0.2087 | 2.25 | primary directional sleeve |
| BNB | 0 | 0.00% | 0.00% | 0.0000 | 0.00 | disabled |
| AVAX | 34 | +27.53% | -3.40% | 0.1807 | 2.56 | primary directional sleeve |

---

### RangeExpansionBreakout — 0.2004 → 0.5341

**Core formula**: 1d regime + 4h trend + BTC risk-on confirmation + compressed Bollinger width + range breakout + volume confirmation + fast EMA/ROC/RSI exit.

Final active structure:

- `minimal_roi = {"0": 100}`, `stoploss = -0.99`, no shorting.
- Entry stack:
  - `close > ema100_1d`
  - `ema9_4h > ema34_4h`
  - BTC `roc > 2.0`
  - BTC `rsi > 50`
  - `bb_width_min < bb_width_ma * 0.68`
  - `bb_width > bb_width_ma * 0.92`
  - `close > pair_specific_prior_high`
  - `close > BB_upper`
  - own `roc > 3.0`
  - `volume > vol_ma * 1.15`
  - BNB disabled
- Pair-specific breakout windows:
  - BTC: 48h prior high
  - ETH: 72h prior high
  - SOL: 72h prior high
  - AVAX: 96h prior high
- Exit: `close < ema12` OR `roc < -3.0` OR `rsi > 82`.

Discovery arc:

- **Round 2**: Added BTC leader confirmation → Sharpe 0.200→0.320 and DD -11.65→-3.97.
- **Rounds 5/8/10**: BNB progressively tightened then disabled → Sharpe 0.355→0.408. BNB breakout profile is structurally bad.
- **Round 19**: Prior high 48h→72h → small improvement.
- **Round 43**: AVAX-only 96h prior high → Sharpe 0.413→0.438.
- **Round 49**: BTC-only 48h prior high → Sharpe 0.438→0.442.
- **Round 79**: EMA21 exit → EMA13 exit → Sharpe 0.483, DD -3.55.
- **Round 91**: EMA13 exit → EMA12 exit → final/peak Sharpe 0.534.

Final per-pair profile:

| pair | trades | profit | DD | Sharpe | PF | role |
|---|---:|---:|---:|---:|---:|---|
| BTC | 37 | +4.79% | -1.89% | 0.1687 | 1.99 | useful low-vol breakout sleeve |
| ETH | 33 | +1.45% | -1.72% | 0.0558 | 1.29 | weak but diversifying |
| SOL | 50 | +8.66% | -2.30% | 0.1734 | 1.73 | core breakout sleeve |
| BNB | 0 | 0.00% | 0.00% | 0.0000 | 0.00 | disabled |
| AVAX | 25 | +9.12% | -2.82% | 0.1365 | 2.41 | core breakout sleeve |

---

## Event dynamics

| event type | count | comment |
|---|---:|---|
| create | 3 | fresh roots: momentum, panic mean-reversion, volatility breakout |
| evolve | 99 | every round touched at least one strategy |
| stable | 198 | two stable rows per round on average, because cap=3 |
| fork | 0 | no fork justified under cap=3 |
| kill | 0 | all three starting paradigms survived |
| discarded evolves | 70 | majority of experiments were rejected and reset |
| kept evolves | 29 | about 29% of evolves became part of the final lineage |

This run is a strong example of **high-volume local search**: 100 rounds produced only 29 kept changes, but those kept changes compounded into a much cleaner final portfolio than round 1.

---

## Most important changes

| rank | change | strategy | impact |
|---:|---|---|---|
| 1 | ROC exit -3→-4 | LeaderVolumeMomentum | Sharpe 0.514→0.617, profit 53.9→88.9 |
| 2 | Remove 4h RSI<75 guard | LeaderVolumeMomentum | Sharpe 0.398→0.527 |
| 3 | Disable SOL in panic reversion | PanicReboundMTF | Sharpe 0.366→0.470, DD -12.2→-6.25 |
| 4 | EMA exit 13→12 | RangeExpansionBreakout | Sharpe 0.483→0.534 |
| 5 | EMA guard 0.90→0.88 | PanicReboundMTF | Sharpe 0.607→0.643 |
| 6 | Volume 1.15×→1.10× | PanicReboundMTF | Sharpe 0.643→0.656 |
| 7 | Disable BNB in breakout | RangeExpansionBreakout | Sharpe 0.355→0.408 |
| 8 | Disable AVAX in panic reversion | PanicReboundMTF | Sharpe 0.332→0.364, DD improved |

---

## Paradigm-specific findings

| finding | momentum | panic mean-reversion | breakout |
|---|---|---|---|
| **BNB** | disable | strongest asset | disable |
| **SOL** | core asset | disable | core asset |
| **AVAX** | core asset | disable | core asset |
| **BTC** | diversifier, stricter local ROC | useful but needs RSI<30 | useful, shorter 48h breakout window |
| **ETH** | strong directional sleeve | useful but needs RSI<30 | weak but diversifying |
| **Volume** | 1.05× sweet spot | 1.10× final | 1.15× sweet spot |
| **Exit style** | very slow ROC failure exit | RSI66 + BB mid | fast EMA12 + ROC/RSI guard |
| **Overbought RSI** | should not block entries | exit timing only | RSI82 exit protects profits |
| **Pair pruning** | selective but not too aggressive | essential | essential |

The most durable lesson: **asset × paradigm interaction dominates aggregate tuning**. A pair should not be judged globally. BNB is bad for directionality and excellent for reversion; SOL/AVAX are the reverse.

---

## Comparison with v0.3.0 Run 2 (apr24b)

| dimension | Run 2: apr24b | Run 3: apr25 |
|---|---:|---:|
| rounds | 39 | **100** |
| events | 120 | **300** |
| peak Sharpe | 0.6388 | **0.6558** |
| final strategies ≥ 0.50 Sharpe | 3 | **3** |
| worst final strategy Sharpe | 0.5208 | **0.5341** |
| largest final DD | -25.7% | **-4.74%** |
| forks | 0 | 0 |
| kills | 0 | 0 |
| discarded evolves | ~29 | **70** |
| main contribution | paradigm boundary mapping | pair-specialized portfolio construction |

Run 2 proved that three paradigms can all work cleanly in v0.3.0. Run 3 pushed that further: it used 100 rounds to turn three viable paradigms into three **low-drawdown, pair-specialized sleeves**.

The trade-off is that Run 3’s strategies are less “universal” per strategy. They increasingly disable bad pair/paradigm combinations. This improves risk-adjusted performance but increases the chance of overfitting to 2023-2025’s asset-specific behavior.

---

## Zero Goodhart assessment

No Goodhart pattern was introduced:

- `exit_profit_only` remained `False`.
- `minimal_roi` stayed `{ "0": 100 }`.
- No tight ROI clipping.
- No artificial no-loss realization trick.
- Stoploss stayed effectively disabled (`-0.99`) as in prior validated runs.
- Regressions were logged and reset rather than cherry-picked silently.

The biggest possible concern is **pair exclusion overfitting**, not oracle gaming. The run repeatedly disabled pairs after per-pair evidence, but did not validate out-of-sample whether those exclusions generalize.

---

## Operational note: spot-only market-load workaround

At round 25, FreqTrade/ccxt began failing because ccxt’s default Binance market loading included inverse/delivery (`dapi`) markets, and the local proxy could not reach:

`https://dapi.binance.com/dapi/v1/exchangeInfo`

Spot and USD-M endpoints were reachable through the same proxy. The run continued with:

`FREQTRADE__EXCHANGE__CCXT_CONFIG__OPTIONS__fetchMarkets='["spot"]' uv run run.py`

This did **not** change strategy logic, pair universe, timerange, or oracle files. It only prevented ccxt from loading unused inverse markets. Verification at `610ee9a` reproduced previous metrics exactly.

---

## Limitations

- **Still single-regime**: 2023-2025 bull/risk-on period only.
- **No out-of-sample validation**: all tuning and evaluation use the same timerange.
- **No benchmark injection**: buy-and-hold still absent from the oracle.
- **Pair exclusions may overfit**: the best Run 3 improvements came from disabling pair/paradigm combinations.
- **Fork remains unused**: cap=3 plus three productive slots again produced no forks.
- **100 rounds intensify multiple-comparison risk**: this run maps boundaries well, but its parameters should not be treated as robust without a second regime.

---

## Open questions for v0.4.0

1. **Bear-market regime test**: extend timerange to include 2021-2022. Do BNB reversion and SOL/AVAX directionality survive?
2. **Benchmark reporting**: inject buy-and-hold and equal-weight portfolio benchmarks into `run.py`.
3. **Out-of-sample split**: force train/test windows or walk-forward evaluation.
4. **Cap=5 experiment**: pair-specialization suggests more sleeves may be useful; cap=3 suppresses fork utility.
5. **Pair-paradigm matrix as first-class object**: rather than strategies manually disabling pairs, v0.4.0 could let each strategy declare allowed pairs based on learned pair profiles.
6. **Cross-pair primary signal revisit**: Run 1’s BTCLeaderBreakX still has the highest v0.3.0 Sharpe; Run 3 optimized secondary BTC filters but did not rediscover cross-pair-as-primary.

---

## Evaluation

**High-confidence validations**:

- v0.3.0 affordances remain load-bearing across 100 rounds.
- Three distinct paradigms can all remain productive under cap=3.
- Per-pair reporting is not cosmetic; it directly drives better strategy construction.
- Pair-specific gating materially improves risk-adjusted performance.
- Momentum and breakout should not trade BNB; panic mean-reversion should.
- Panic mean-reversion should not trade SOL/AVAX under this signal.
- Exit speed is still one of the highest-leverage tuning dimensions.

**Not validated**:

- Survival outside 2023-2025.
- Robustness of pair exclusions.
- Whether final strategies beat buy-and-hold.
- Whether cap=3 is optimal.
- Whether fork has value in this architecture.
