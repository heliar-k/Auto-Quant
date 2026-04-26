"""
BTCLeaderBreakout — cross-pair primary signal: BTC 4h breakout triggers all pairs

Paradigm: cross-pair-primary
Hypothesis: BTC 4h Donchian breakout with ATR expansion is a leading indicator for
            the entire crypto market. When BTC breaks above its 10-period 4h high
            with expanding ATR, altcoins follow within hours. Using BTC's breakout
            as the PRIMARY entry trigger (not just a filter) should capture these
            co-movement events earlier than waiting for each pair's independent signal.
            This revisits Run 1's BTCLeaderBreakX paradigm that achieved Sharpe ~1.07
            but was never re-explored in Runs 2 or 3.
Parent: root (Run 1 lineage: BTCLeaderBreakX)
Created: pending
Status: active
Uses MTF: yes (4h BTC Donchian + ATR, cross-pair primary trigger)
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class BTCLeaderBreakout(IStrategy):
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

    startup_candle_count: int = 200

    @informative("4h", "BTC/USDT")
    def populate_indicators_btc_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["dc_high10"] = dataframe["high"].rolling(10).max()
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_ma20"] = dataframe["atr"].rolling(20).mean()
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=12)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        btc_break = (
            dataframe["btc_usdt_close_4h"] > dataframe["btc_usdt_dc_high10_4h"].shift(1)
        ) & (
            dataframe["btc_usdt_close_4h"].shift(1) <= dataframe["btc_usdt_dc_high10_4h"].shift(1)
        )

        entry_condition = (
            btc_break
            & (dataframe["btc_usdt_atr_4h"] > dataframe["btc_usdt_atr_ma20_4h"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.5)
        )

        if metadata.get("pair") == "BTC/USDT":
            entry_condition &= dataframe["btc_usdt_atr_4h"] > dataframe["btc_usdt_atr_ma20_4h"] * 1.2

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema21"])
            | (dataframe["roc"] < -1.0),
            "exit_long",
        ] = 1
        return dataframe
