"""
BTCMomentumLeader — BTC 4h momentum surge triggers entries on all pairs

Paradigm: cross-pair-primary
Hypothesis: BTC 4h momentum surges (ROC>threshold) signal market-wide directional
episodes. Unlike Donchian breakouts (absolute price levels), ROC-based triggers
capture the rate of change — a BTC momentum burst often precedes altcoin moves
regardless of absolute price level. Local 1h trend + volume confirmation ensures
the altcoin is participating in the move.
Parent: root
Created: 9761eed
Status: active
Uses MTF: yes (BTC 4h ROC, local 4h EMA trend, 1d EMA200 regime)
Exit Mechanism: dual exit — close<EMA21 OR ROC<-1.5 (BNB disabled)
Exit Rationale: BTC momentum-led moves fade when BTC momentum decelerates.
EMA21 catches structural trend break; ROC<-2.0 catches the momentum failure
before the EMA signal confirms. Dual exit is paradigm-appropriate because
BTC-led altcoin moves have both a trend component and a momentum component
"""

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy, informative


class BTCMomentumLeader(IStrategy):
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
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=6)
        return dataframe

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        return dataframe

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=10)
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        btc_momentum_surge = dataframe["btc_usdt_roc_4h"] > 5.0
        local_trend = (
            (dataframe["close"] > dataframe["ema200_1d"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["ema9_4h"] > dataframe["ema21_4h"])
        )
        volume_ok = dataframe["volume"] > dataframe["vol_ma"] * 1.5

        entry_condition = btc_momentum_surge & local_trend & volume_ok & (dataframe["roc"] > 3.0)

        if metadata.get("pair") == "BNB/USDT":
            entry_condition &= False

        dataframe.loc[entry_condition, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema21"])
            | (dataframe["roc"] < -1.5),
            "exit_long",
        ] = 1
        return dataframe
