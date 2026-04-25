"""
LeaderVolumeMomentum — BTC-confirmed momentum with volume participation

Paradigm: momentum
Hypothesis: 1h momentum in the 5-pair crypto universe is most reliable when it is
confirmed by BTC's own 1h strength, aligned with the traded pair's 4h EMA trend,
and accompanied by above-normal volume. This tests whether BTC still acts as the
leader/follower gate once SOL, BNB, and AVAX are added to the universe.
Parent: root
Created: e772907
Status: active
Uses MTF: yes (4h trend + cross-pair BTC ROC)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class LeaderVolumeMomentum(IStrategy):
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

    startup_candle_count: int = 180

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    @informative("1h", "BTC/USDT")
    def populate_indicators_btc(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=20)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["rsi_4h"] < 75)
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["roc"] > 7.0)
            & (dataframe["btc_usdt_roc_1h"] > 4.0)
            & (dataframe["btc_usdt_rsi_1h"] > 50)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.05)
        )

        if metadata.get("pair") == "BNB/USDT":
            entry_condition &= False

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["roc"] < -2.0, "exit_long"] = 1
        return dataframe