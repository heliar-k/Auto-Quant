"""
CrossPairMomentum — BTC momentum-gated entries on all 5 pairs

Paradigm: momentum
Hypothesis: Among the 5-pair universe, momentum propagates from BTC to altcoins with
a measurable delay. By gating altcoin entries on BTC's own momentum being positive,
we can avoid entering altcoin trends that lack macro confirmation. This strategy
exercises the cross-pair @informative affordance — pulling BTC's 1h data while trading
every pair (including BTC itself, where it becomes self-referential).
Parent: root
Created: (set after first commit)
Status: active
Uses MTF: yes (cross-pair BTC + 4h trend filter)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class CrossPairMomentum(IStrategy):
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
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        return dataframe

    @informative("1h", "BTC/USDT")
    def populate_indicators_btc(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=20)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["roc"] > 7.0)
            & (dataframe["btc_usdt_roc_1h"] > 4.0)
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["volume"] > dataframe["vol_ma"]),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["roc"] < -2, "exit_long"] = 1
        return dataframe
