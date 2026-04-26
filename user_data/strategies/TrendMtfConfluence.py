"""
TrendMtfConfluence — multi-timeframe trend-following with pullback entries

Paradigm: trend-following
Hypothesis: Strong trends on 1h crypto are identified by 1d EMA200 regime +
4h EMA9>21 trend alignment. Entries on 1h RSI pullbacks (35-48) within this
aligned structure capture trend continuation while avoiding momentum-chasing
entries. The MTF stack acts as a regime gate: only trade pullbacks when the
higher-timeframe trend is intact.
Parent: root
Created: a38cfb7
Status: active
Uses MTF: yes (1d EMA200 regime, 4h EMA trend)
Exit Mechanism: RSI>78 (overbought exhaustion) OR 4h EMA9<EMA21 (trend break)
Exit Rationale: trend-following exits must balance two risks — exiting too
early clips the trend, exiting too late surrenders gains. RSI>78 only triggers
at genuine overbought extremes (confirmed optimum from v0.3.0 bracketing at
70/75/78/80). The 4h EMA cross catches structural trend failure that RSI
alone would miss, making the exit robust to both exhaustion and reversal
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class TrendMtfConfluence(IStrategy):
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
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=10)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["close"] > dataframe["ema200_1d"])
            & (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["rsi"] >= 28)
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
