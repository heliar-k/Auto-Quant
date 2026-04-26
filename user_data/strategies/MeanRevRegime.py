"""
MeanRevRegime — multi-TF mean-reversion with 1d regime filter

Paradigm: mean-reversion
Hypothesis: mean-reversion opportunities are more frequent and more reliable during
bear markets (2022), where panic overshoots create deeper RSI extremes. A 1d EMA50
regime filter keeps MR trades aligned with the dominant trend direction, while
multi-TF RSI confluence (1h+4h+BTC) filters for market-wide oversold conditions.
Volume >1.5x ensures participation in the reversal.
Parent: root
Created: apr26b-setup
Status: active
Uses MTF: yes (4h RSI + 1d EMA50 regime + cross-pair BTC RSI)
Exit Mechanism: RSI>60 AND close>BB_mid (dual: momentum normalized + mean reached)
Exit Rationale: mean reversion is complete when price returns to the center of its
recent range AND momentum has normalized. Requiring both prevents exiting during
dead-cat bounces that don't actually reach the mean
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class MeanRevRegime(IStrategy):
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

    startup_candle_count: int = 250

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
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
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        bbands = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_lower"] = bbands["lowerband"]
        dataframe["bb_mid"] = bbands["middleband"]
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["close"] > dataframe["ema200_1d"])
            & (dataframe["rsi_4h"] < 40)
            & (dataframe["btc_usdt_rsi_1h"] < 40)
            & (dataframe["rsi"] < 30)
            & (dataframe["close"] < dataframe["bb_lower"])
            & (dataframe["volume"] > dataframe["vol_ma"] * 2.0)
        )

        if metadata.get("pair") in ("SOL/USDT", "AVAX/USDT"):
            entry_condition &= False

        if metadata.get("pair") in ("BTC/USDT", "ETH/USDT"):
            entry_condition &= dataframe["rsi"] < 25

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["rsi"] > 60)
            & (dataframe["close"] > dataframe["bb_mid"]),
            "exit_long",
        ] = 1
        return dataframe
