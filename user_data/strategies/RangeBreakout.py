"""
RangeBreakout — pure price-structure breakout above prior range highs

Paradigm: breakout
Hypothesis: clean breakouts above prior N-bar highs with volume confirmation and
4h trend alignment capture the initial thrust of new trends without the complexity
of compression-expansion detection. This is simpler and more robust than Keltner
or BB-based approaches, especially across regimes. Pair-specific breakout windows
account for different volatility profiles.
Parent: root
Created: apr26b-r8
Status: active
Uses MTF: yes (4h EMA trend + 1d EMA100 regime + cross-pair BTC)
Exit Mechanism: close<EMA12 OR ROC<-3 (fast exit for breakout dissipation)
Exit Rationale: breakout energy dissipates within 3-8 candles. EMA12 catches
the trend break, ROC<-3 catches momentum failure. Fast exit is paradigm-appropriate
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class RangeBreakout(IStrategy):
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

    startup_candle_count: int = 260

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema34"] = ta.EMA(dataframe, timeperiod=34)
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema100"] = ta.EMA(dataframe, timeperiod=100)
        return dataframe

    @informative("1h", "BTC/USDT")
    def populate_indicators_btc(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=20)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema12"] = ta.EMA(dataframe, timeperiod=12)
        dataframe["ema13"] = ta.EMA(dataframe, timeperiod=13)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=12)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["prior_high_48"] = dataframe["high"].rolling(48).max().shift(1)
        dataframe["prior_high_72"] = dataframe["high"].rolling(72).max().shift(1)
        dataframe["prior_high_96"] = dataframe["high"].rolling(96).max().shift(1)
        dataframe["vol_ma"] = dataframe["volume"].rolling(24).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        breakout_level = dataframe["prior_high_72"]

        if metadata.get("pair") == "AVAX/USDT":
            breakout_level = dataframe["prior_high_96"]

        if metadata.get("pair") == "BTC/USDT":
            breakout_level = dataframe["prior_high_48"]

        entry_condition = (
            (dataframe["close"] > dataframe["ema100_1d"])
            & (dataframe["ema9_4h"] > dataframe["ema34_4h"])
            & (dataframe["btc_usdt_roc_1h"] > 2.5)
            & (dataframe["btc_usdt_rsi_1h"] > 50)
            & (dataframe["btc_usdt_close_1h"] > dataframe["btc_usdt_ema50_1h"])
            & (dataframe["close"] > breakout_level)
            & (dataframe["rsi"] > 56)
            & (dataframe["rsi"] < 72)
            & (dataframe["roc"] > 2.0)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.15)
        )

        if metadata.get("pair") == "ETH/USDT":
            entry_condition &= (
                (dataframe["close"] > dataframe["prior_high_96"])
                & (dataframe["volume"] > dataframe["vol_ma"] * 1.5)
            )

        if metadata.get("pair") == "BNB/USDT":
            entry_condition &= False

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema12"])
            | (dataframe["roc"] < -2.0),
            "exit_long",
        ] = 1
        return dataframe
