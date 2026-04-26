"""
KeltnerExpansion — Keltner Channel compression-expansion volatility breakout

Paradigm: volatility
Hypothesis: Keltner Channels (ATR-based) respond faster to volatility regime shifts
than Bollinger Bands (stddev-based), potentially providing earlier entry signals
during compression→expansion transitions. This tests a new indicator family against
the multi-regime 2021-2025 period, including the 2022 bear where volatility patterns
differ sharply from bull markets.
Parent: root
Created: apr26b-setup
Status: active
Uses MTF: yes (4h EMA trend + 1d EMA100 regime + cross-pair BTC)
Exit Mechanism: close<EMA12 OR ROC<-3 (fast dual exit for volatility dissipation)
Exit Rationale: volatility expansion breakouts dissipate energy quickly (3-8 candles).
Fast EMA12 catches trend break, ROC<-3 catches momentum failure. Waiting for slow
exits would surrender breakout gains
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class KeltnerExpansion(IStrategy):
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
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema12"] = ta.EMA(dataframe, timeperiod=12)
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        atr = ta.ATR(dataframe, timeperiod=20)
        dataframe["kc_upper"] = dataframe["ema20"] + 1.5 * atr
        dataframe["kc_lower"] = dataframe["ema20"] - 1.5 * atr
        dataframe["kc_width"] = (dataframe["kc_upper"] - dataframe["kc_lower"]) / dataframe["ema20"]
        dataframe["kc_width_ma"] = dataframe["kc_width"].rolling(96).mean()
        dataframe["kc_width_min"] = dataframe["kc_width"].rolling(96).min()
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=12)
        dataframe["prior_high_48"] = dataframe["high"].rolling(48).max().shift(1)
        dataframe["prior_high_72"] = dataframe["high"].rolling(72).max().shift(1)
        dataframe["prior_high_96"] = dataframe["high"].rolling(96).max().shift(1)
        dataframe["vol_ma"] = dataframe["volume"].rolling(24).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        was_compressed = dataframe["kc_width_min"] < dataframe["kc_width_ma"] * 0.72
        is_expanding = dataframe["kc_width"] > dataframe["kc_width_ma"] * 0.85
        breakout_level = dataframe["prior_high_72"]

        if metadata.get("pair") == "AVAX/USDT":
            breakout_level = dataframe["prior_high_96"]

        if metadata.get("pair") == "BTC/USDT":
            breakout_level = dataframe["prior_high_48"]

        entry_condition = (
            (dataframe["close"] > dataframe["ema100_1d"])
            & (dataframe["ema9_4h"] > dataframe["ema34_4h"])
            & (dataframe["btc_usdt_roc_1h"] > 1.0)
            & (dataframe["btc_usdt_rsi_1h"] > 45)
            & was_compressed
            & is_expanding
            & (dataframe["close"] > breakout_level)
            & (dataframe["close"] > dataframe["kc_upper"])
            & (dataframe["roc"] > 2.0)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.05)
        )

        if metadata.get("pair") == "BNB/USDT":
            entry_condition &= (
                (dataframe["close"] > dataframe["prior_high_96"])
                & (dataframe["volume"] > dataframe["vol_ma"] * 1.3)
            )

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema12"])
            | (dataframe["roc"] < -3.0),
            "exit_long",
        ] = 1
        return dataframe
