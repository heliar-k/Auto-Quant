"""
MeanRevRSI — RSI mean-reversion on 1h across 5 pairs

Paradigm: mean-reversion
Hypothesis: In the 5-pair universe at 1h, price tends to revert from RSI extremes within
a few days. This is the same hypothesis that produced a clean Sharpe ~0.52 in v0.2.0 on
BTC+ETH. Adding SOL/BNB/AVAX tests whether the reversion behavior generalizes across
assets. Per-pair reporting will reveal which pairs revert reliably and which don't.
Parent: root
Created: (set after first commit)
Status: active
Uses MTF: yes (1d EMA50 regime + 4h RSI confluence)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class MeanRevRSI(IStrategy):
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

    startup_candle_count: int = 200

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.2, nbdevdn=2.2)
        dataframe["bb_lower"] = bb["lowerband"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] > dataframe["ema50_1d"])
            & (dataframe["rsi_4h"] < 45)
            & (dataframe["rsi"] < 32)
            & (dataframe["close"] < dataframe["bb_lower"]),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["rsi"] > 65, "exit_long"] = 1
        return dataframe
