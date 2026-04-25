"""
PanicReboundMTF — MTF panic mean-reversion across the 5-pair universe

Paradigm: mean-reversion
Hypothesis: Crypto majors revert best after synchronized weakness: a local 1h
oversold/BB-lower event is higher quality when the traded pair is below-neutral on
4h RSI, BTC is also materially washed out on 1h, and the pair remains in a constructive 1d
EMA50 regime. This tests whether v0.3.0's cross-pair + MTF context can separate
recoverable panic from genuine trend failure.
Parent: root
Created: e772907
Status: active
Uses MTF: yes (1d EMA50, 4h RSI, cross-pair BTC RSI)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class PanicReboundMTF(IStrategy):
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

    startup_candle_count: int = 220

    @informative("1h", "BTC/USDT")
    def populate_indicators_btc(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=12)
        return dataframe

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        bbands = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.2, nbdevdn=2.2)
        dataframe["bb_lower"] = bbands["lowerband"]
        dataframe["bb_mid"] = bbands["middleband"]
        dataframe["vol_ma"] = dataframe["volume"].rolling(24).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["close"] > dataframe["ema50_1d"])
            & (dataframe["close"] > dataframe["ema50"] * 0.88)
            & (dataframe["rsi_4h"] < 50)
            & (dataframe["btc_usdt_rsi_1h"] < 40)
            & (dataframe["btc_usdt_roc_1h"] < 1.5)
            & (dataframe["rsi"] < 32)
            & (dataframe["close"] < dataframe["bb_lower"])
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.15)
        )

        if metadata.get("pair") == "AVAX/USDT":
            entry_condition &= False

        if metadata.get("pair") == "SOL/USDT":
            entry_condition &= False

        if metadata.get("pair") == "ETH/USDT":
            entry_condition &= dataframe["rsi"] < 30

        if metadata.get("pair") == "BTC/USDT":
            entry_condition &= dataframe["rsi"] < 30

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["rsi"] > 66)
            & (dataframe["close"] > dataframe["bb_mid"]),
            "exit_long",
        ] = 1
        return dataframe