"""
BTCLeaderBreakout — BTC 4h Donchian breakout triggers entries on all pairs

Paradigm: cross-pair-primary
Hypothesis: BTC 4h Donchian channel breakouts with ATR expansion signal
market-wide directional moves. When BTC breaks out, altcoins follow with
amplified moves. Using BTC as the primary trigger (not just a filter) with
local 1h trend + volume confirmation captures the leader/follower dynamic.
Pair-agnostic entry conditions allow diversification across all 5 pairs.
Parent: root
Created: TBD
Status: active
Uses MTF: yes (BTC 4h Donchian+ATR, local 4h trend, 1d regime)
Exit Mechanism: dual exit — close<EMA21 OR ROC<-1.0
Exit Rationale: BTC-led breakouts fade predictably when BTC momentum stalls.
EMA21 catches the trend break; ROC<-1.0 catches momentum failure before the
EMA signal. Dual exit is load-bearing for cross-pair-primary because the
leader's momentum decay appears in both price structure AND rate-of-change
before altcoins fully respond
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

    startup_candle_count: int = 280

    @informative("4h", "BTC/USDT")
    def populate_indicators_btc_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["dc_high"] = dataframe["high"].rolling(10).max().shift(1)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_ma"] = dataframe["atr"].rolling(20).mean()
        return dataframe

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=10)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_ma"] = dataframe["atr"].rolling(20).mean()
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        btc_breakout = dataframe["close"] > dataframe["btc_usdt_dc_high_4h"]
        btc_atr_expanding = dataframe["btc_usdt_atr_4h"] > dataframe["btc_usdt_atr_ma_4h"]
        local_trend = (
            (dataframe["close"] > dataframe["ema50"])
            & (dataframe["ema9_4h"] > dataframe["ema21_4h"])
        )
        volume_ok = dataframe["volume"] > dataframe["vol_ma"] * 1.5

        entry_condition = btc_breakout & btc_atr_expanding & local_trend & volume_ok

        if metadata.get("pair") == "BTC/USDT":
            entry_condition &= dataframe["atr"] > dataframe["atr_ma"] * 1.2

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema21"])
            | (dataframe["roc"] < -1.0),
            "exit_long",
        ] = 1
        return dataframe
