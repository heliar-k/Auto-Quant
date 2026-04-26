"""
KeltnerBreakout — Keltner Channel breakout with ATR-based bands

Paradigm: breakout
Hypothesis: Keltner Channels (EMA + ATR-based bands) capture breakouts differently
than Bollinger Bands — ATR adapts to volatility while BB expands with deviation.
When price breaks above the upper Keltner band with 4h trend alignment, it signals
genuine directional expansion rather than volatility noise. The ATR midline exit
captures the momentum burst without waiting for full trend exhaustion.
Parent: root
Created: 5799a6f
Status: active
Uses MTF: yes (4h EMA trend, 1d EMA200 regime)
Exit Mechanism: close < EMA20 (Keltner midline break)
Exit Rationale: Keltner breakouts represent short-duration directional bursts.
Exiting at the midline (EMA20) captures the expansion's core move — by the time
price reaches the lower band, the breakout energy has already dissipated. Fast
exit preserves gains from the initial expansion phase
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class KeltnerBreakout(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.99
    trailing_stop = False
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 300

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        atr = ta.ATR(dataframe, timeperiod=10)
        dataframe["kc_upper"] = dataframe["ema20"] + 2.5 * atr
        dataframe["kc_lower"] = dataframe["ema20"] - 2.5 * atr
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=10)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["close"] > dataframe["ema200_1d"])
            & (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["close"] > dataframe["kc_upper"])
            & (dataframe["roc"] > 4.0)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.5)
        )

        if metadata.get("pair") == "BNB/USDT":
            entry_condition &= (
                (dataframe["roc"] > 6.0)
                & (dataframe["volume"] > dataframe["vol_ma"] * 2.0)
            )

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema20"])
            | (dataframe["roc"] < -2.0),
            "exit_long",
        ] = 1
        return dataframe
