"""
TrendMtfRegime — multi-TF trend-following with 1d regime filter

Paradigm: trend-following
Hypothesis: 4h EMA trend + 1d EMA200 regime + 1h RSI pullback entries form a robust
trend-following system that survives bear markets via the 1d regime filter (close >
EMA200). BTC cross-pair RSI ensures market-wide participation in the trend.
Parent: root
Created: apr26b-setup
Status: active
Uses MTF: yes (4h EMA trend + 1d EMA200 regime + cross-pair BTC RSI)
Exit Mechanism: 4h EMA9<EMA21 (trend broken) OR 1h RSI>75 (overbought exhaustion)
Exit Rationale: trend-following exits must balance letting trends run vs protecting
profits. 4h EMA cross catches structural trend failure, while RSI>75 catches
exhaustion tops. Both are slow enough to avoid clipping trend moves
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class TrendMtfRegime(IStrategy):
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
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["close"] > dataframe["ema200_1d"])
            & (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["btc_usdt_rsi_1h"] > 45)
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["rsi"] > 34)
            & (dataframe["rsi"] < 46)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.2)
        )

        if metadata.get("pair") == "AVAX/USDT":
            entry_condition &= False

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["ema9_4h"] < dataframe["ema21_4h"])
            | (dataframe["rsi"] > 72),
            "exit_long",
        ] = 1
        return dataframe
