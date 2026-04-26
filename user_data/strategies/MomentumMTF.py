"""
MomentumMTF — 4h-trend-aligned 1h momentum with volume participation

Paradigm: momentum
Hypothesis: Directional momentum is most reliable when the 4h trend is aligned
            (EMA9 > EMA21), the 1h ROC shows strong immediate thrust, and volume
            confirms participation. Unlike mean-reversion, this targets continuation
            — strong moves tend to persist in a bull regime. Run 3 showed SOL/AVAX
            excel at directional strategies while BNB underperforms. This strategy
            starts unconstrained and lets the experiment loop discover pair-specific
            thresholds.
Parent: root
Created: pending
Status: active
Uses MTF: yes (4h EMA trend)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class MomentumMTF(IStrategy):
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

    startup_candle_count: int = 120

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
        entry_condition = (
            (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["roc"] > 5.0)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.2)
        )

        if metadata.get("pair") == "BNB/USDT":
            entry_condition &= False

        if metadata.get("pair") == "ETH/USDT":
            entry_condition &= dataframe["roc"] > 7.0
            entry_condition &= dataframe["volume"] > dataframe["vol_ma"] * 1.5

        if metadata.get("pair") == "AVAX/USDT":
            entry_condition &= dataframe["roc"] > 7.0
            entry_condition &= dataframe["volume"] > dataframe["vol_ma"] * 1.5

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["roc"] < -3.0, "exit_long"] = 1
        return dataframe
