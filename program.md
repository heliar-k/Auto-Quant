# Auto-Quant v0.4.0 — multi-regime + out-of-sample + cap=5 + exit-as-design

Four structural improvements on top of v0.3.x's validated 4-paradigm foundation:

1. **Multi-regime backtesting**: extend timerange to 2021-2026, covering bear + bull.
2. **Out-of-sample validation**: train on 2023-2024, test on 2025-2026 Q1.
3. **Cap=5**: raise hard cap from 3 to 5 active strategies.
4. **Exit-as-design**: exit mechanism as a first-class design decision.

---

## What's new in v0.4.0

### 1. Multi-regime backtesting

All v0.3.x runs used 2023-2025 only — a nearly uninterrupted bull market. No
strategy was ever tested in a bear market. v0.4.0 extends data to cover
**2021-01-01 → 2026-01-29**: the 2021 bull, 2022 bear, and 2023-2025 recovery.

New data required:
- 2021-01-01 to 2022-12-31 for all 15 files (5 pairs × 3 timeframes)
- `prepare.py` handles this

Key questions the extended regime answers:
- Does BTCLeaderBreakout (cross-pair primary) survive when BTC breakouts fail?
- Does momentum collapse in trend reversals?
- Does mean-reversion improve in bear markets (as theory predicts)?
- Are pair exclusions (SOL/AVAX in panic, BNB in momentum) stable across regimes?

### 2. Out-of-sample validation

All v0.3.x tuning used the full timerange for both iteration and evaluation.
v0.4.0 splits into:

| period | timerange | purpose |
|---|---|---|
| **train** | `20230101-20241231` | experiment loop — all iteration happens here |
| **test** | `20250101-20260129` | held out — single validation after loop concludes |

The experiment loop runs exclusively on the train period. After the loop
concludes, strategies are validated once on the test period. No parameter
tuning on test data — pure evaluation.

`run.py` accepts an optional `--timerange` argument to override the default
(train) timerange for final validation.

### 3. Cap=5

v0.3.x validated 4 distinct paradigms:
- Cross-pair primary (BTCLeaderBreakout, Sharpe 0.91)
- Momentum (MomentumMTF, Sharpe 0.83)
- Mean-reversion (PanicReboundMTF, Sharpe 0.66)
- Volatility breakout (RangeExpansionBreakout, Sharpe 0.53)

Cap=3 prevented all four from coexisting, and fork was used only once across
197 combined rounds. Cap=5 allows all validated paradigms to form a permanent
portfolio plus one experimental slot for new ideas.

### 4. Exit mechanism as first-class design object

v0.3.1's single clearest finding: exit mechanisms are paradigm-specific.

| exit pattern | cross-pair primary | momentum | mean-reversion |
|---|---|---|---|
| dual exit (EMA+ROC) | **+0.02** Sharpe | **-0.29** Sharpe | n/a |
| pure ROC | untested | **baseline** | n/a |
| RSI+BB conditional | n/a | n/a | **baseline** |

v0.4.0 requires each strategy to declare its exit logic as a primary design
decision — alongside paradigm and entry signal — with explicit rationale
linking exit mechanism to paradigm. Exit is not a post-hoc tuning parameter.

---

## Foundation (v0.3.x)

This is an experiment to have the LLM do its own quantitative research across
**multiple parallel strategies** that can combine signals across **multiple
timeframes** (1h base + 4h + 1d) and **multiple assets** (5-pair universe with
cross-asset signal references).

v0.3.0 (3 runs, 178 rounds) proved MTF + cross-pair affordances are load-bearing
and asset × paradigm interaction dominates aggregate tuning. v0.3.1 (1 run, 19
rounds) resurrected cross-pair-as-primary as a 4th paradigm (Sharpe 0.91) and
injected buy-and-hold benchmark reporting into `run.py`.

The core bet of v0.2.0 was multi-strategy: maintaining up to 3 strategies in
parallel resisted single-paradigm anchoring. That worked — see
`versions/0.2.0/retrospective.md`. v0.3.0 opened multi-timeframe, multi-asset,
and per-pair reporting. v0.4.0 opens multi-regime, out-of-sample validation,
cap=5, and exit-as-design.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `may1`).
   The branch `autoresearch/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current `master`.
3. **Read the in-scope files**. The repo is small. Read these files for full context:
   - `README.md` — repository context
   - `config.json` — fixed FreqTrade config (pairs, timeframe, fees).
   - `prepare.py` — data download.
   - `run.py` — the batch backtest oracle.
   - `user_data/strategies/_template.py.example` — skeleton for new strategies.
     **Note:** the folder may also contain `__pycache__`; ignore it.
   - `versions/0.1.0/retrospective.md` and `versions/0.2.0/retrospective.md`
     — previous runs' findings. Both are valuable: v0.1.0 documents the
     single-paradigm anchoring failure mode + 3 Goodhart exploits the agent
     eventually rolled back. v0.2.0 documents the multi-strategy response
     and 5 paradigms tested (3 with clean positive edge).
   - `versions/0.3.0/retrospective.md` — 3-run synthesis: pair-specialized
     portfolio construction, 5 paradigms tested.
   - `versions/0.3.1/retrospective.md` — cross-pair primary signal validation,
     exit paradigm-specificity, benchmark injection.
4. **Verify data exists**: Check that needed data files exist under
   `user_data/data/`. For the full multi-regime run:
   - `BTC_USDT-{1h,4h,1d}.feather`
   - `ETH_USDT-{1h,4h,1d}.feather`
   - `SOL_USDT-{1h,4h,1d}.feather`
   - `BNB_USDT-{1h,4h,1d}.feather`
   - `AVAX_USDT-{1h,4h,1d}.feather`

   Data must cover at least the train period (`20230101-20241231`).
   For the full multi-regime run, data should cover `20210101-20260129`.
   If any are missing, tell the user to run `uv run prepare.py`.
5. **Initialize results.tsv**: Create `results.tsv` with just the header row:
   ```
   commit	event	strategy_name	sharpe	max_dd	note
   ```
   Tab-separated. Do not commit this file — it's gitignored on purpose.
6. **Create 1-5 starting strategies.** This is the most important setup step.
   - Each strategy goes in its own file: `user_data/strategies/<YourName>.py`
   - Class name MUST match filename stem (FreqTrade requirement)
   - Each strategy's docstring MUST fill all 8 metadata fields:
     Paradigm, Hypothesis, Parent, Created, Status, Uses MTF, Exit Mechanism, Exit Rationale
   - **Each strategy MUST target a different paradigm.** Don't create 5
     mean-reversion variants as a "safe start." Pick from: mean-reversion,
     trend-following, momentum, volatility, breakout, cross-pair-primary,
     other. At least 3 different categories.
   - **Strongly encouraged**: at least one strategy should use each of the
     major affordances: MTF, cross-pair, and pair-specific gates.
   - **Exit mechanism is a primary design field.** Each strategy must state
     its exit logic and explain why it fits the paradigm (see "Exit as design"
     section below).
   - Keep each strategy minimal initially. You'll iterate in the loop.
7. **Confirm and go**: Confirm setup looks good with the user.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each round runs a backtest on ALL active strategies on the **train timerange**
(`20230101-20241231`) across the **5-pair portfolio** (BTC, ETH, SOL, BNB,
AVAX) at 1h base. `run.py` emits one `---` summary block per strategy plus
a `__benchmark__` block, containing both portfolio-aggregate metrics AND
per-pair breakdown.

### What you CAN do

- Modify any file under `user_data/strategies/` (that isn't prefixed `_`)
- Create a new strategy file
- Delete a strategy file (via `git rm`)
- Copy an existing strategy to create a variant (fork)

### What you CANNOT do

- Modify `prepare.py`. This is the data download contract.
- `uv add` new dependencies. Use what's already in `pyproject.toml`.
- Call the `freqtrade` CLI directly. The only way to run backtests is via
  `uv run run.py`.
- Modify the pair list or `_template.py.example`.
- Request timeframes other than `1h`, `4h`, `1d` OR pairs other than the
  5 in the whitelist in `@informative` decorators. Anything else will crash
  the backtest with a missing-data error.

### What you can modify (v0.4.0 expanded)

- `config.json`: `max_open_trades` may be adjusted if cap changes.
- `run.py`: the `TIMERANGE` constant and train/test configuration may be
  modified for v0.4.0's time-split infrastructure. Core backtest logic
  (strategy discovery, metric extraction, benchmark injection) remains
  unchanged.

### Train/test split (new in v0.4.0)

The experiment loop runs on the **train period** (`20230101-20241231`).
The **test period** (`20250101-20260129`) is held out.

- **During the loop**: all backtests use the train timerange. All evolve,
  fork, kill decisions are based on train metrics only.
- **After the loop**: strategies are validated once on the test period:
  ```
  uv run run.py --timerange 20250101-20260129 > run-test.log 2>&1
  ```
- Do NOT tune parameters on test results. The test validation is a single
  pass for reporting. If a strategy performs well on train but poorly on
  test, flag it as overfit in the retrospective.

### Multi-timeframe + cross-asset affordance

Data is pre-downloaded for **three timeframes × five pairs = 15 combinations**
(plus extended history for multi-regime):

| Timeframe | Pairs |
|---|---|
| 1h (base) | BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT, AVAX/USDT |
| 4h | BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT, AVAX/USDT |
| 1d | BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT, AVAX/USDT |

Strategies are always evaluated on the 1h base across ALL five pairs in one
backtest run. You cannot change the base TF or pair list. But you can pull
additional context along TWO axes via FreqTrade's `@informative` decorator:
higher-TF data from the same pair, and same-TF data from different pairs.

**Basic higher-timeframe usage** (most common):

```python
from freqtrade.strategy import IStrategy, informative

class YourStrategy(IStrategy):
    timeframe = "1h"

    @informative("4h")
    def populate_indicators_4h(self, dataframe, metadata):
        dataframe["rsi"] = ta.RSI(dataframe, 14)
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe, metadata):
        dataframe["ema200"] = ta.EMA(dataframe, 200)
        return dataframe

    def populate_indicators(self, dataframe, metadata):
        # Merged columns are auto-available: rsi_4h, ema200_1d
        dataframe["rsi"] = ta.RSI(dataframe, 14)
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        # MTF confluence: 1h oversold + 4h not overbought + 1d bull regime
        dataframe.loc[
            (dataframe["rsi"] < 20)
            & (dataframe["rsi_4h"] < 60)
            & (dataframe["close"] > dataframe["ema200_1d"]),
            "enter_long",
        ] = 1
        return dataframe
```

**Cross-pair usage** (reference another asset's data):

```python
@informative("1h", "BTC/USDT")
def populate_btc_1h(self, dataframe, metadata):
    dataframe["close_ma"] = ta.SMA(dataframe, 50)
    return dataframe

# In populate_indicators on, say, ETH — you now have `btc_usdt_close_ma_1h`
# Column naming: `{base}_{quote}_{col}_{tf}`, lowercase, underscore-separated.
```

For truly symmetric cross-pair strategies (e.g., BTC/ETH ratio that means
something on BOTH pairs), use `informative_pairs()` with a
`metadata['pair']`-conditional branch inside `populate_indicators`.

**Key properties** (FreqTrade handles these for you):
- Column naming: `rsi` in a `@informative('4h')` method → `rsi_4h` in 1h dataframe.
  For cross-pair: `rsi` in `@informative('1h', 'BTC/USDT')` → `btc_usdt_rsi_1h`.
- Look-ahead safe: FreqTrade shifts merged data by 1 period so current 1h bar
  never sees future higher-TF bars.
- Forward-filled: at any 1h bar, the merged `rsi_4h` value is the last
  fully-closed 4h bar's RSI.

**When to use higher TFs:**
- Regime filters (`close > ema200_1d` for bull regime)
- Trend confirmation (`ema9_4h > ema21_4h`)
- Volatility context (`atr_4h` for relative-vol positioning)

**When to use cross-pair:**
- Leader/follower dynamics (BTC often leads ETH/altcoins on 4h)
- Diversification checks ("only enter if BTC isn't crashing")
- Cross-pair primary signal (BTC breakout triggers entries on all altcoins)

**When NOT to use either:**
- If the paradigm doesn't have an intuitive MTF/cross-pair analog, don't force it.

**`startup_candle_count`** — bump up for slow indicators on higher TFs. EMA200
on 1d needs 200 daily bars = 4800 hourly bars of warmup. Starting at 250-300
is usually safe for most MTF configurations.

### Exit as design (new in v0.4.0)

Each strategy's docstring MUST include two additional fields:

```
Exit Mechanism: <brief description of exit logic>
Exit Rationale: <why this exit fits this paradigm>
```

Examples of paradigm-exit fit:

| paradigm | well-matched exit | rationale |
|---|---|---|
| cross-pair primary | dual: EMA21 + ROC | BTC-led moves fade predictably; fast exit catches momentum failure |
| momentum | slow: pure ROC -3 | trends have pullbacks; premature exit clips winners |
| mean-reversion | conditional: RSI + BB mid | mean reversion completes when price returns to center |
| volatility breakout | fast: EMA12 + RSI guard | breakout energy dissipates quickly; fast exit protects profits |

An ill-matched exit (e.g., EMA21 on momentum) can destroy performance
regardless of entry quality. The exit rationale must be explicit and
defensible before the strategy enters the experiment loop.

### Per-pair reporting

`run.py` output includes a `per_pair:` section after the aggregate
metrics. Example:

```
---
strategy:         YourStrategy
sharpe:           0.45         # aggregate across all 5 pairs
...
pairs:            BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,AVAX/USDT
per_pair:
  BTC/USDT: sharpe=0.62 trades=45 profit_pct=18.5 dd_pct=-3.2 wr=58.0 pf=1.72
  ETH/USDT: sharpe=0.38 trades=50 profit_pct=12.1 dd_pct=-5.1 wr=52.0 pf=1.35
  SOL/USDT: sharpe=0.12 trades=35 profit_pct=5.3 dd_pct=-8.1 wr=48.6 pf=1.08
  BNB/USDT: sharpe=0.71 trades=40 profit_pct=22.0 dd_pct=-2.9 wr=62.5 pf=1.93
  AVAX/USDT: sharpe=-0.05 trades=30 profit_pct=-2.8 dd_pct=-7.4 wr=46.7 pf=0.92
```

**Use per-pair metrics aggressively** — they're the main new information
surface. Things to look for:
- **Does the strategy work on ALL pairs or just some?** A paradigm that's
  great on BTC but negative on SOL/AVAX is either (a) BTC-specific
  (interesting, worth understanding why) or (b) noise (worth killing).
- **Are DDs asymmetric?** Some pairs may carry most of the portfolio DD.
- **Trade count balance**: if one pair has 200 trades and another has 3,
  that's a sample-size problem you should note.
- **Cross-pair correlations in edge**: BTC+BNB doing well while ETH+SOL+AVAX
  flat tells you something about what kind of regime the strategy exploits.

In your `results.tsv` notes, when a result varies substantially across pairs,
**call it out explicitly** — e.g., "Sharpe 0.45 aggregate but SOL=-0.10 and
BNB=+0.80; signal is BNB-heavy, trade count 40 not enough". These are the
observations that make the run's knowledge output per-asset-profile-shaped.

### Hard rules on strategy lifecycle

**Rule 1: Hard cap — 5 active strategies.**
At any moment, `user_data/strategies/` must contain at most 5 non-underscore
`.py` files. To add a 6th, you must first `git rm` one of the existing.

**Rule 2: Stagnation gate — 3 stable rounds.**
Each round, every strategy gets one of these events logged in `results.tsv`:
- `create` — you added it this round
- `evolve` — you modified it this round
- `stable` — it existed, got measured, but you didn't touch it
- `fork` — you copied it to create a derivative (logged on the child, with
  `parent→child` in the strategy_name field)
- `kill` — you removed it this round

**If a strategy has accumulated 3 consecutive `stable` events with no `evolve`
or `fork`, the next round it MUST receive one of: `evolve`, `fork`, or `kill`.**
Cannot sit idle for a 4th stable round. You decide which treatment. This rule
exists because the cap is limited — we can't afford a slot sitting still.

**Rule 3: Every round must touch at least one strategy.**
A round where all events are `stable` is not an experiment — it's wasted time.
At minimum, evolve one strategy per round. (Exception: the very first backtest
round right after setup, where you log `create` events for what you built.)

**Rule 4: Paradigm diversity at setup.**
See setup step 6 above. First 1-5 strategies must target different paradigms.
After that, you're free to create same-paradigm variants (e.g. two
mean-reversion approaches with different signals) — but sparingly. Diversity
is more valuable than depth.

**Rule 5: Exit rationale required.**
Every strategy created or forked in v0.4.0 must include `Exit Mechanism` and
`Exit Rationale` fields in its docstring. Existing strategies carried over
from v0.3.x should have these fields added before any evolution.

## Output format

Once `run.py` finishes, stdout has one `---` block per strategy, plus a
`__benchmark__` block, like:

```
---
strategy:         MeanRevRSI
commit:           abc1234
timerange:        20230101-20241231
sharpe:           0.8234
sortino:          1.0412
calmar:           0.5821
total_profit_pct: 45.3210
max_drawdown_pct: -8.9123
trade_count:      142
win_rate_pct:     54.2300
profit_factor:    1.6700
pairs:            BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,AVAX/USDT
per_pair:
  BTC/USDT: sharpe=0.6200 trades=45 profit_pct=18.50 dd_pct=-3.20 wr=58.0 pf=1.72
  ...

---
strategy:                __benchmark__
type:                    buy-and-hold
timerange:               20230101-20241231
equal_weight_profit_pct: XXX.XX
equal_weight_dd_pct:     -XX.XX
per_pair:
  BTC/USDT: profit_pct=XXX.XX dd_pct=-XX.XX
  ...
```

If a strategy crashes, its block looks like:
```
---
strategy:         SomeBrokenStrategy
commit:           abc1234
status:           ERROR
error_type:       NameError
error_msg:        name 'foo' is not defined
traceback:
  ...
```

Extract all strategies' metrics at once:
```bash
grep "^---\|^strategy:\|^sharpe:\|^trade_count:\|^max_drawdown_pct:" run.log
```

Full per-strategy block:
```bash
awk '/^---$/,/^$/' run.log
```

## Logging results

After each round, append one row to `results.tsv` **per strategy touched**.
Tab-separated, 6 columns:

```
commit	event	strategy_name	sharpe	max_dd	note
```

Rules:
- `commit` is the short git hash of the round's commit
- `event` is one of `create | evolve | stable | fork | kill`
- For `fork`, `strategy_name` uses `parent→child` format (e.g. `MeanRevRSI→MRVolGate`)
- For `kill`, leave `sharpe` and `max_dd` as `-` (dash). The strategy is gone.
- `note` is your reasoning in free text. This is load-bearing — when you
  later decide keep vs kill, you re-read these notes. Be specific:
  - Bad: `"tried MACD, didn't work"`
  - Good: `"replaced RSI entry with MACD cross-up. wr 68→51, sharpe 0.82→0.31. MACD crossovers on 1h crypto trigger inside ongoing drops, catching knives. Discarding paradigm."`
- Every strategy that exists this round gets a row, even if `stable`. This
  is how the stagnation counter stays visible.

**Do NOT commit `results.tsv`.** It is gitignored on purpose — the log
survives `git reset --hard`, which is essential so you don't forget what
you've already tried.

## The experiment loop

The experiment runs on the dedicated branch (e.g. `autoresearch/may1`).

LOOP FOREVER:

1. **Look at state**: read `results.tsv` (tail ~30 rows), note the current
   active strategies and their stagnation counters (how many consecutive
   `stable` events each has).

2. **Decide this round's action.** Your toolkit per round:
   - `evolve <strategy>`: modify an existing strategy file
   - `create <name>`: add a new strategy (if cap has room)
   - `fork <parent>→<child>`: cp a strategy file to a new name, then modify
     the child
   - `kill <strategy>`: `git rm` the file
   - You can combine: e.g. "kill A and create B in the same commit" (make room
     for something new), or "fork A→A' and evolve B" (two strategies touched)

3. **Respect the rules.** In particular:
   - Cap: max 5 active strategies after this round's changes
   - Stagnation: any strategy with 3 prior consecutive `stable` events must
     be evolved, forked, or killed THIS round
   - Every round touches ≥ 1 strategy

4. **Make the code changes.** Write/modify files under `user_data/strategies/`.

5. **`git commit -am "<short summary of this round>"`**

6. **Run the backtest**: `uv run run.py > run.log 2>&1`

7. **Read the summary**: `awk '/^---$/,/^$/' run.log` (shows all blocks) or
   `grep "^---\|^strategy:\|^sharpe:\|^trade_count:" run.log` (compact).

8. **Check for crashes**: a strategy with `status: ERROR` needs to be fixed
   (if the error is trivial — syntax, typo) OR killed (if the hypothesis is
   broken). Don't leave ERROR strategies around.

9. **Log to results.tsv**: one row per strategy that existed this round. Fill
   in the event, metrics (or `-` for kills), and your reasoning note.

10. **Decide keep vs rollback.**
    - Common case: per-strategy decisions happen inline (you either evolved
      to something better, or the change was bad and you git-reset only that
      strategy's commit). The whole round doesn't have one "keep/discard"
      decision — individual strategies do.
    - If the whole round was a mistake (broke everything, wrong direction),
      `git reset --hard HEAD~1` to undo all changes.
    - If some strategies improved and others didn't: keep the commit, log
      `stable` for the unchanged ones, log `evolve` or `kill` etc. for the
      changed ones.

11. **Loop.**

### Deciding keep vs kill on a strategy

A strategy deserves to stay if:
- It has positive edge (Sharpe > 0, profit factor > 1) with meaningful trade
  count (>20 trades over 2 years of train data)
- Its paradigm is distinct from what the other active strategies cover
- Recent evolutions have moved it in the right direction
- Its exit mechanism aligns with its paradigm

A strategy deserves to die if:
- It's been stable for 3 rounds with no improvement and you don't have a new
  idea for it
- Its paradigm overlaps strongly with another active strategy that's doing
  better
- You need its slot for a fresh paradigm you want to try
- It's consistently negative and further tweaks won't help
- Its exit mechanism is misaligned with its paradigm and structural fixes fail

**Always log your reasoning.** These notes become the retrospective —
future you (and the meta-analysis layer) will read them to extract what this
run actually learned.

### Final validation (new in v0.4.0)

After the experiment loop concludes:

1. **Run on test timerange**: `uv run run.py --timerange 20250101-20260129 > run-test.log 2>&1`
2. **Compare train vs test metrics**: flag strategies with large performance
   gaps as potentially overfit.
3. **Run on full timerange** (optional): `uv run run.py --timerange 20210101-20260129 > run-full.log 2>&1`
   for a multi-regime performance picture spanning the 2021 bull, 2022 bear,
   and 2023-2025 recovery.
4. **Document regime-specific behavior**: which strategies survive the bear?
   Which thrive? These observations are the main knowledge output of v0.4.0.

### Goodhart watch

From v0.1.0 we learned the agent can inadvertently game the metric:
- `exit_profit_only=True` → 100% win rate by never realizing losses
  (regime-dependent, breaks in bear markets)
- Tight `minimal_roi` clipping → tiny uniform returns → low stddev → huge
  Sharpe (profit goes DOWN even as Sharpe goes UP)

**v0.2.0, v0.3.0, and v0.3.1 added zero new Goodhart exploits — try to keep that streak.**

If you find a Sharpe jump that comes with a profit drop or a DD collapse to
~0, that's a gaming signal, not real edge. Log it, document the mechanism,
then either kill the strategy or explicitly note "this is an oracle artifact,
not edge" in the description.

Multi-strategy helps here: if strategy A's Sharpe jumps while B and C stay
flat on the same data, A's jump is more likely a real discovery. If ALL
strategies' Sharpe jumped on the same commit — you probably modified
something shared, or the oracle itself has a hole.

With the train/test split, overfitting becomes more detectable: a strategy
that looks great on train but fails on test is likely overfit, not genuinely
good. Flag such cases prominently in the retrospective.

**Timeout**: each full round (5 strategies × backtest) should take under 5
minutes. If a single run exceeds 10 minutes, kill it and treat it as a
failure (revert the commit, skip the round).

### NEVER STOP

Once the experiment loop has begun (after initial setup), do NOT pause to
ask the human if you should continue. Do NOT ask "should I keep going?" or
"is this a good stopping point?". The human may be asleep, or away from
the computer, and expects you to continue working *indefinitely* until
manually stopped.

If you run out of ideas:
- **Re-read all retrospectives** (`versions/0.1.0/`, `0.2.0/`, `0.3.0/`,
  `0.3.1/`) — each documents specific open questions and untested directions
- Apply multi-regime thinking: "would this change help in a bear market?"
- Apply exit-as-design thinking: "is this exit mechanism paradigm-appropriate?"
- Look at your stagnant strategies — can you fork them with a bolder change?
- Try combining winners from different paradigms
- Try completely new indicator families you haven't touched
- Check the paradigm-specific findings tables in each retrospective for
  transferable insights

The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep.
Each round of 5-strategy backtests takes ~3-5 minutes, so you can run several
dozen per hour. The user then wakes up to a rich multi-strategy research
trace ready for meta-analysis.
