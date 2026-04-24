"""
TrendMtfConfluence — 1h pullback entries in the direction of higher-TF trends

Paradigm: trend-following
Hypothesis: BTC/ETH/SOL/BNB/AVAX 1h price exhibits directional bias from higher-timeframe
trends. Entering pullbacks in the direction of 4h and 1d trends should capture directional
moves while filtering out counter-trend noise. This is the classic MTF confluence approach
adapted to crypto 1h.
Parent: root
Created: (set after first commit)
Status: active
Uses MTF: yes (4h trend + 1d regime filter)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class TrendMtfConfluence(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.25

    trailing_stop = False
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 200

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_sma"] = dataframe["atr"].rolling(14).mean()
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] > dataframe["ema200_1d"])
            & (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["atr_4h"] > dataframe["atr_sma_4h"])
            & (dataframe["rsi"] > 36)
            & (dataframe["rsi"] < 47),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["rsi"] > 70)
            | (dataframe["ema9_4h"] < dataframe["ema21_4h"]),
            "exit_long",
        ] = 1
        return dataframe
