"""
SuperTrendPullback — SuperTrend trend-following with 1d regime + pullback entry

Paradigm: trend-following
Hypothesis: SuperTrend (ATR-based) captures trend direction more responsively than
EMA-based systems, but the apr26 run's -63.5% DD proved it needs a 1d EMA200 regime
filter. With the regime filter, SuperTrend pullbacks should catch strong directional
moves while avoiding bear-market entries. This tests whether a different trend
indicator (SuperTrend vs EMA) adds diversification to the portfolio.
Parent: root
Created: apr26b-r15
Status: active
Uses MTF: yes (4h EMA trend + 1d EMA200 regime)
Exit Mechanism: SuperTrend flip bearish OR RSI>72 (dual: structural stop + take-profit)
Exit Rationale: SuperTrend flip signals trend termination (structural stop). RSI>72
catches overbought exhaustion within the trend. Dual exit is paradigm-appropriate
for ATR-based trend following — SuperTrend provides the structural stop while RSI
provides profit-taking that the slow SuperTrend flip would miss
"""

from pandas import DataFrame
import numpy as np
import talib.abstract as ta

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
        atr = ta.ATR(dataframe, timeperiod=10)
        hl2 = (dataframe["high"] + dataframe["low"]) / 2.0
        upper_band = hl2 + 3.0 * atr
        lower_band = hl2 - 3.0 * atr

        n = len(dataframe)
        final_upper = np.full(n, np.nan)
        final_lower = np.full(n, np.nan)
        direction = np.zeros(n)

        close_arr = dataframe["close"].values
        upper_arr = upper_band.values
        lower_arr = lower_band.values

        for i in range(10, n):
            if i == 10:
                final_upper[i] = upper_arr[i]
                final_lower[i] = lower_arr[i]
                direction[i] = 1.0 if close_arr[i] > upper_arr[i] else -1.0
                continue

            if upper_arr[i] < final_upper[i - 1] or close_arr[i - 1] > final_upper[i - 1]:
                final_upper[i] = upper_arr[i]
            else:
                final_upper[i] = final_upper[i - 1]

            if lower_arr[i] > final_lower[i - 1] or close_arr[i - 1] < final_lower[i - 1]:
                final_lower[i] = lower_arr[i]
            else:
                final_lower[i] = final_lower[i - 1]

            if direction[i - 1] > 0:
                direction[i] = -1.0 if close_arr[i] < final_lower[i] else 1.0
            else:
                direction[i] = 1.0 if close_arr[i] > final_upper[i] else -1.0

        dataframe["st_direction"] = direction
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        st_bullish = dataframe["st_direction"] > 0
        st_just_flipped = dataframe["st_direction"].shift(1) <= 0

        entry_condition = (
            st_bullish
            & st_just_flipped
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["rsi"] > 25)
            & (dataframe["rsi"] < 60)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.1)
        )

        if metadata.get("pair") == "AVAX/USDT":
            entry_condition &= False

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["st_direction"] < 0)
            | (dataframe["rsi"] > 72),
            "exit_long",
        ] = 1
        return dataframe
