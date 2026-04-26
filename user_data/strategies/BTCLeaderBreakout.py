"""
BTCLeaderBreakout — BTC 4h Donchian breakout as cross-pair primary signal

Paradigm: cross-pair-primary
Hypothesis: BTC 4h Donchian-20 breakouts with ATR expansion serve as a leading
indicator for altcoin entries. When BTC breaks out of a 20-period range with
above-average volatility, the entire crypto market tends to follow within hours.
This paradigm was validated in v0.3.1 (Sharpe 0.91 on 2023-2025) but failed
on the 2023-2024-only train period in apr26. The multi-regime 2021-2025 period
should provide enough BTC-led breakout episodes for the paradigm to work.
Parent: root
Created: apr26b-setup
Status: active
Uses MTF: yes (BTC 4h Donchian + local 4h trend + 1d regime)
Exit Mechanism: close<EMA21 OR ROC<-2 (dual: trend break + momentum fade)
Exit Rationale: cross-pair breakouts fade predictably when the leader's momentum
stalls. EMA21 catches the structural trend break, while ROC<-2 catches the
momentum failure that precedes it. The v0.3.1 optimum was ROC=-1.0; starting
at -2.0 for multi-regime robustness
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

    startup_candle_count: int = 250

    @informative("4h", "BTC/USDT")
    def populate_indicators_btc_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["donchian_high"] = dataframe["high"].rolling(20).max().shift(1)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_ma"] = dataframe["atr"].rolling(20).mean()
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["volume_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema100"] = ta.EMA(dataframe, timeperiod=100)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=12)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        btc_breakout = (
            dataframe["btc_usdt_close_4h"] > dataframe["btc_usdt_donchian_high_4h"]
        )
        btc_vol_expand = (
            dataframe["btc_usdt_atr_4h"] > dataframe["btc_usdt_atr_ma_4h"]
        )
        btc_volume_ok = (
            dataframe["btc_usdt_volume_4h"] > dataframe["btc_usdt_volume_ma_4h"] * 1.15
        )

        entry_condition = (
            (dataframe["close"] > dataframe["ema100_1d"])
            & btc_breakout
            & btc_vol_expand
            & btc_volume_ok
            & (dataframe["ema9_4h"] > dataframe["ema21_4h"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["volume"] > dataframe["vol_ma"] * 1.2)
        )

        if metadata.get("pair") == "BTC/USDT":
            entry_condition &= (
                dataframe["btc_usdt_atr_4h"] > dataframe["btc_usdt_atr_ma_4h"] * 1.2
            )

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema21"])
            | (dataframe["roc"] < -1.3),
            "exit_long",
        ] = 1
        return dataframe
