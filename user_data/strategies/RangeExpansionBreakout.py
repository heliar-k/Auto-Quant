"""
RangeExpansionBreakout — volatility expansion after compressed ranges

Paradigm: volatility
Hypothesis: SOL/BNB/AVAX-style crypto trends often begin as range compression followed
by volume-backed expansion. A breakout above a prior 48h high should work only when
4h trend is positive, BTC is confirming market-wide risk appetite, 1h Bollinger width
is expanding from a compressed state, and volume confirms participation. This tests a
distinct volatility/breakout paradigm instead of another RSI or ROC variant.
Parent: root
Created: e772907
Status: active
Uses MTF: yes (4h EMA trend + 1d EMA regime + cross-pair BTC momentum)
Exit Mechanism: fast dual-condition (close<EMA12 OR ROC<-3)
Exit Rationale: breakout energy dissipates quickly; three independent failure
detectors (trend break, momentum fade, overbought exhaustion) each capture a
different failure mode — waiting for a single slow exit would surrender the
gains from the initial expansion
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class RangeExpansionBreakout(IStrategy):
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

    startup_candle_count: int = 240

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
        dataframe["ema13"] = ta.EMA(dataframe, timeperiod=13)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=12)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        bbands = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bbands["upperband"]
        dataframe["bb_lower"] = bbands["lowerband"]
        dataframe["bb_mid"] = bbands["middleband"]
        dataframe["bb_width"] = (dataframe["bb_upper"] - dataframe["bb_lower"]) / dataframe["bb_mid"]
        dataframe["bb_width_ma"] = dataframe["bb_width"].rolling(96).mean()
        dataframe["bb_width_min"] = dataframe["bb_width"].rolling(96).min()
        dataframe["prior_high_48"] = dataframe["high"].rolling(48).max().shift(1)
        dataframe["prior_high"] = dataframe["high"].rolling(72).max().shift(1)
        dataframe["prior_high_96"] = dataframe["high"].rolling(96).max().shift(1)
        dataframe["vol_ma"] = dataframe["volume"].rolling(24).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        was_compressed = dataframe["bb_width_min"] < dataframe["bb_width_ma"] * 0.68
        is_expanding = dataframe["bb_width"] > dataframe["bb_width_ma"] * 0.92
        breakout_level = dataframe["prior_high"]

        if metadata.get("pair") == "AVAX/USDT":
            breakout_level = dataframe["prior_high_96"]

        if metadata.get("pair") == "BTC/USDT":
            breakout_level = dataframe["prior_high_48"]

        entry_condition = (
            (dataframe["close"] > dataframe["ema100_1d"])
            & (dataframe["ema9_4h"] > dataframe["ema34_4h"])
            & (dataframe["btc_usdt_roc_1h"] > 2.0)
            & was_compressed
            & is_expanding
            & (dataframe["close"] > breakout_level)
            & (dataframe["close"] > dataframe["bb_upper"])
            & (dataframe["roc"] > 3.0)
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.15)
        )

        if metadata.get("pair") == "BNB/USDT":
            entry_condition &= (
                (dataframe["close"] > dataframe["prior_high_96"])
                & (dataframe["volume"] > dataframe["vol_ma"] * 1.5)
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