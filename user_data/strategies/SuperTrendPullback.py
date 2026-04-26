"""
SuperTrendPullback — SuperTrend trend detection with RSI pullback entries

Paradigm: trend-following
Hypothesis: SuperTrend (ATR-based trailing stop) provides cleaner trend detection
than EMA crosses on 1h crypto because it adapts to volatility. When SuperTrend
is bullish and 1d EMA200 confirms the macro regime, buying RSI pullbacks within
the trend captures continuation with lower heat than breakout-chasing entries.
Parent: root
Created: TBD
Status: active
Uses MTF: yes (1d EMA200 regime)
Exit Mechanism: SuperTrend flips bearish OR RSI>75 (trend exhaustion)
Exit Rationale: SuperTrend flip is the primary structural exit — when the
ATR-based stop reverses, the trend is objectively broken. RSI>75 provides a
secondary exit for overbought conditions within an intact trend, taking profits
before the SuperTrend signal (which lags by design)
"""

from pandas import DataFrame
import talib.abstract as ta
import numpy as np

from freqtrade.strategy import IStrategy, informative


class SuperTrendPullback(IStrategy):
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

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        atr = ta.ATR(dataframe, timeperiod=10)
        hl_avg = (dataframe["high"] + dataframe["low"]) / 2
        multiplier = 3.0
        dataframe["st_upper"] = hl_avg + multiplier * atr
        dataframe["st_lower"] = hl_avg - multiplier * atr
        # SuperTrend bullish: close above st_lower after being above it
        dataframe["st_bullish"] = dataframe["close"] > dataframe["st_lower"].shift(1)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["close"] > dataframe["ema200_1d"])
            & dataframe["st_bullish"]
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["rsi"] >= 30)
            & (dataframe["rsi"] <= 50)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.1)
        )

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            ~dataframe["st_bullish"]
            | (dataframe["rsi"] > 75),
            "exit_long",
        ] = 1
        return dataframe
