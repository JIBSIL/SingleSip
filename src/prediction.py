import requests
import iso8601
import pandas as pd
import numpy as np

import src.trade as tradeutil
import src.process_data as process_data
import src.evaluate_model as evaluate_model
import src.telegram_bot as telegram


def get_recent_data(ticker, apikey):
    apiurl = f"https://rest.coinapi.io/v1/exchangerate/{ticker}/USD/history"

    req = requests.get(
        apiurl,
        params={"period_id": "4HRS", "limit": 75},
        headers={"X-CoinAPI-Key": apikey},
    )

    json_rate_raw = req.json()

    # prune bad data
    json_rate = []
    for eachdata in json_rate_raw:
        if eachdata["rate_open"] != 0:
            json_rate.append(eachdata)
    stats = []
    # i = 0
    for item in json_rate:
        # for some reason i have to modify time to make it pandas compatible
        time = f'{item["time_close"].split(".")[0]}Z'
        timestamp = int(iso8601.parse_date(time).timestamp() * 1000)
        individual = [timestamp, item["rate_close"]]
        stats.append(individual)

    stats.reverse()
    return stats


def execute_trade(
    predicted_price,
    actual_price,
    balance,
    btc_balance,
    constant_data,
    changing_data,
    trader,
    liquidate=False,
):
    trading_fee, ticker, max_investment, max_trade = constant_data
    trades_buy, trades_sell, trades = changing_data

    # max_trade = 0.4
    trade_amount = balance * max_trade  # Trading max_trade% of the balance
    if trade_amount > max_investment:
        trade_amount = max_investment

    # Buy BTC
    if predicted_price > actual_price:
        if trade_amount < 0.1:
            # can't trade less than 10 cents
            return balance, btc_balance, changing_data
        trades_buy += 1
        btc_bought = trade_amount / actual_price
        fee = btc_bought * trading_fee
        btc_balance += btc_bought - fee
        balance -= trade_amount

        trader.buy(trade_amount)

        print(f"Bought {round(trade_amount, 2)}")

    # Sell BTC
    elif predicted_price < actual_price:
        if liquidate:
            max_trade = 1
        btc_sold = btc_balance * max_trade
        gain = btc_sold * actual_price
        if gain < 0.1:
            # can't trade less than 10 cents
            return balance, btc_balance, changing_data

        trader.sell((btc_sold * 0.99))  # leave 1% in so the trade goes through

        print(
            f'{"Selling" if liquidate == False else "Liquidating"} {btc_sold} {ticker} (${round(gain, 2)})'
        )
        fee = gain * trading_fee
        balance += gain - fee
        btc_balance -= btc_sold
        trades_sell += 1
    else:
        print("Prediction == target price! Holding")

    trades += 1

    changing_data = (trades_buy, trades_sell, trades)

    return balance, btc_balance, changing_data


class Predictor:
    def __init__(
        self,
        ticker,
        lookback,
        apikey,
        model,
        trader: tradeutil.Trader,
        constant_data,
        telegram_bot: telegram.TelegramBot,
    ):
        self.ticker = ticker
        self.lookback = lookback
        self.apikey = apikey
        self.model = model
        self.trader = trader
        self.constant_data = constant_data
        self.telegram_bot = telegram_bot

        # setup changing data
        trades_buy = 0
        trades_sell = 0
        trades = 0
        self.changing_data = (trades_buy, trades_sell, trades)

    def trade(self):
        data = get_recent_data(self.ticker, self.apikey)
        balance, btc_balance = self.trader.get_balances()
        df_merged = process_data.process_data(data)
        df_scaled, scaler = process_data.add_technical_indicators(
            df_merged, self.lookback, 0
        )

        features = df_scaled[
            [
                "3_day_avg_price",
                "tsi",
                "rsi",
                "sharpe_ratio",
                "Bollinger_Upper",
                "Bollinger_Lower",
            ]
        ]
        target = df_scaled[["PRICE"]]
        X_data, y_data = process_data.create_dataset(
            pd.concat([target, features], axis=1), self.lookback
        )

        print(f"Short historical dataset shape: {X_data.shape}")

        num_features, num_features_backtest = evaluate_model.get_num_features()

        prediction_scaled = self.model.predict(X_data)

        predicted_price_tomorrow = scaler.inverse_transform(
            np.concatenate(
                (
                    prediction_scaled[len(prediction_scaled) - 1].reshape(-1, 1),
                    np.zeros((1, num_features_backtest)),
                ),
                axis=1,
            )
        )[0, 0]
        actual_price_today = data[len(data) - 1][1]
        predicted_change = (
            predicted_price_tomorrow - actual_price_today
        ) / actual_price_today

        print(
            f"Model predicts market change will be {round(predicted_change * 100, 2)}%"
        )

        if predicted_change < -0.1:
            balance, btc_balance, changing_data_returned = execute_trade(
                predicted_price_tomorrow,
                actual_price_today,
                balance,
                btc_balance,
                self.constant_data,
                self.changing_data,
                self.trader,
                True,
            )
            self.changing_data = changing_data_returned

            self.telegram_bot.send_message(
                f"⚠️ LIQUIDATION: Market change will be {round(predicted_change * 100, 2)}%. Liquidating {self.ticker} now."
            )

            print(
                f"Liquidation executed. {self.ticker} Balance: {round(btc_balance, 5)}, USD Balance: {round(balance, 2)}"
            )
        elif abs(predicted_change) > 0.01:
            balance, btc_balance, changing_data_returned = execute_trade(
                predicted_price_tomorrow,
                actual_price_today,
                balance,
                btc_balance,
                self.constant_data,
                self.changing_data,
                self.trader,
            )
            self.changing_data = changing_data_returned

            if predicted_change < 0:
                self.telegram_bot.send_message(
                    f"⚠️ SELL: 📉 Market change will be {round(predicted_change * 100, 2)}%. Selling {self.ticker} now."
                )
            else:
                self.telegram_bot.send_message(
                    f"✅ BUY: 📈 Market change will be {round(predicted_change * 100, 2)}%. Buying {self.ticker} now."
                )

            print(
                f"Trade executed. {self.ticker} Balance: {round(btc_balance, 5)}, USD Balance: {round(balance, 2)}"
            )
