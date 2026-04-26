"""
MomentumADX — momentum with ADX trend-strength confirmation

Paradigm: momentum
Hypothesis: ADX trend-strength filtering (ADX>25, +DI>-DI) suppresses momentum
entries during directionless/choppy markets where ROC-based signals generate false
positives. This is especially important in bear markets (2022) where ROC spikes
during dead-cat bounces look like momentum but lack ADX confirmation. Tests a new
indicator family not used in prior Auto-Quant runs.
Parent: root
Created: apr26b-setup
Status: active
Uses MTF: yes (4h EMA trend + cross-pair BTC ROC)
Exit Mechanism: ADX<20 (trend exhaustion) OR ROC<-4 (momentum failure)
Exit Rationale: momentum strategies need slow exits to let trends run. ADX-based
exit adds structural confirmation: when ADX drops below 20, the trend has
objectively weakened. ROC<-4 catches momentum failure within an ongoing trend
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class MomentumADX(IStrategy):
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
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["close"] > dataframe["ema200_1d"])
            & (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["adx"] > 25)
            & (dataframe["plus_di"] > dataframe["minus_di"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["roc"] > 5.0)
            & (dataframe["btc_usdt_roc_1h"] > 3.0)
            & (dataframe["btc_usdt_rsi_1h"] > 50)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.2)
        )

        if metadata.get("pair") == "BNB/USDT":
            entry_condition &= False

        if metadata.get("pair") in ("ETH/USDT", "AVAX/USDT"):
            entry_condition &= dataframe["roc"] > 7.0

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["adx"] < 20)
            | (dataframe["roc"] < -4.0),
            "exit_long",
        ] = 1
        return dataframe
