"""
BTCTrendConfirm — MTF trend-following with BTC cross-pair momentum confirmation

Paradigm: trend-following
Hypothesis: The TrendMtfConfluence MTF stack (1d EMA200 + 4h EMA9>21 + 1h RSI
pullback) captures trend continuation, but adding BTC 1h ROC confirmation filters
entries that occur during market-wide weakness. When BTC has positive momentum,
altcoin trend pullbacks are more likely to resume. This tests whether cross-pair
BTC momentum improves entry quality for trend-following.
Parent: TrendMtfConfluence
Created: TBD
Status: active
Uses MTF: yes (1d EMA200 regime, 4h EMA trend, cross-pair BTC ROC)
Exit Mechanism: RSI>78 (overbought exhaustion) OR 4h EMA9<EMA21 (trend break)
Exit Rationale: same as parent — RSI>78 catches overbought extremes, 4h EMA cross
catches structural trend failure. Exit unchanged from parent to isolate the effect
of the BTC confirmation filter on entry quality
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class BTCTrendConfirm(IStrategy):
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

    @informative("1h", "BTC/USDT")
    def populate_indicators_btc(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=20)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=10)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["close"] > dataframe["ema200_1d"])
            & (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["btc_usdt_roc_1h"] > 2.0)
            & (dataframe["rsi"] >= 30)
            & (dataframe["rsi"] <= 52)
        )

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["rsi"] > 78)
            | (dataframe["ema9_4h"] < dataframe["ema21_4h"]),
            "exit_long",
        ] = 1
        return dataframe
