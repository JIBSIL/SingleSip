import numpy as np
import random


def execute_trade(
    predicted_price,
    actual_price,
    actual_price_tomorrow,
    balance,
    btc_balance,
    implied_values,
    liquidate=False,
):
    global initial_balance, stoploss_activated, btc_end_override, trades, trades_sell, trades_buy

    # implied_values: array of values as we're not using outer function variables
    max_slippage, max_investment, trading_fee, ticker = implied_values

    buy_prediction = None
    model_was_right = None

    slippage = random.uniform(0, max_slippage)
    max_trade = 0.2
    trade_amount = balance * max_trade  # Trading max_trade% of the balance
    if trade_amount > max_investment:
        trade_amount = max_investment

    # Buy BTC
    if predicted_price > actual_price:
        if trade_amount < 0.1:
            # can't trade less than 10 cents
            return balance, btc_balance, model_was_right
        trades_buy += 1
        buy_price = actual_price * (1 + slippage)
        btc_bought = trade_amount / buy_price
        fee = btc_bought * trading_fee
        btc_balance += btc_bought - fee
        balance -= trade_amount
        buy_prediction = True
        print(f"Buying {round(trade_amount, 2)}")

    # Sell BTC
    elif predicted_price < actual_price:
        sell_price = actual_price * (1 - slippage)
        if liquidate:
            max_trade = 1
        btc_sold = btc_balance * max_trade
        gain = btc_sold * sell_price
        if gain < 0.1:
            # can't trade less than 10 cents
            return balance, btc_balance, model_was_right
        print(
            f'{"Selling" if liquidate == False else "Liquidating"} {btc_sold} {ticker} (${round(gain, 2)})'
        )
        buy_prediction = False
        fee = gain * trading_fee
        balance += gain - fee
        btc_balance -= btc_sold
        trades_sell += 1
    else:
        print("Prediction == target price! Holding")

    global trades
    trades += 1

    # test if model was right
    if actual_price_tomorrow == None:
        return balance, btc_balance, None

    should_buy = actual_price_tomorrow > actual_price
    if buy_prediction == None:
        model_was_right = None
    else:
        model_was_right = should_buy == buy_prediction

    return balance, btc_balance, model_was_right


def backtest(
    model,
    X_test,
    y_test,
    scaler,
    ticker,
    window,
    lookback,
    num_features,
    num_features_backtest,
):
    global balance, initial_balance, btc_balance, stoploss_activated, btc_end_override, trades, trades_sell, trades_buy

    # Starting parameters
    initial_balance = 100
    balance = initial_balance  # Starting balance in USD
    btc_balance = 0  # Bitcoin balance
    # trading_fee = 0.005  # Trading fee (0.5%)
    # trading_fee = 0
    trading_fee = 0.001015  # poloniex trading fee
    max_slippage = 0.005  # Maximum slippage (0.5%)
    max_investment = 100  # Maximum USD balance for trading
    stoploss_enabled = True
    stoploss = 0.20  # Stoploss at 20%
    stoploss_activated = False
    btc_end_override = False

    trades = 0
    trades_sell = 0
    trades_buy = 0

    # prepare implied values array (does not change)
    implied_values = [max_slippage, max_investment, trading_fee, ticker]

    predictions_scaled = model.predict(X_test)

    # predicted_prices_tomorrow = scaler.inverse_transform(np.concatenate((predictions_scaled, np.zeros((predictions_scaled.shape[0], 2))), axis=1))[:, 0]

    full_array = np.zeros((predictions_scaled.shape[0], num_features))
    full_array[:, :2] = predictions_scaled
    predicted_prices_tomorrow = scaler.inverse_transform(full_array)[:, 0]

    predicted_prices_tomorrow = predicted_prices_tomorrow[1:]
    X_test = X_test[1:]
    y_test = y_test[1:]

    # stats
    model_right_amount = 0
    model_wrong_amount = 0

    btc_usd_balance_if_ending = initial_balance

    # Simulation loop
    for i in range(len(predicted_prices_tomorrow)):
        print(f"Today the portfolio is worth {round(btc_usd_balance_if_ending, 2)}")
        predicted_price_tomorrow = predicted_prices_tomorrow[i]
        actual_price_today = scaler.inverse_transform(
            np.concatenate(
                (y_test[i].reshape(-1, 1), np.zeros((1, num_features_backtest))), axis=1
            )
        )[0, 0]

        # see if we can seek 1 forward
        if (i + 1) < (len(y_test) - 1):
            actual_price_tomorrow = scaler.inverse_transform(
                np.concatenate(
                    (
                        y_test[i + 1].reshape(-1, 1),
                        np.zeros((1, num_features_backtest)),
                    ),
                    axis=1,
                )
            )[0, 0]
        else:
            actual_price_tomorrow = None

        # Check if the predicted change is more than 2%
        predicted_change = (
            predicted_price_tomorrow - actual_price_today
        ) / actual_price_today
        print(
            f"Actual price today: {actual_price_today}, Predicted price tomorrow: {predicted_price_tomorrow}"
        )
        print(
            f"Model predicts market change will be {round(predicted_change * 100, 2)}%"
        )
        if predicted_change < -0.1:
            balance, btc_balance, model_was_right = execute_trade(
                predicted_price_tomorrow,
                actual_price_today,
                actual_price_tomorrow,
                balance,
                btc_balance,
                implied_values,
                True,
            )

            if model_was_right == True:
                model_right_amount += 1
            elif model_was_right == False:
                model_wrong_amount += 1
            # else: the no trade happened

            print(
                f"Liquidation executed. {ticker} Balance: {round(btc_balance, 5)}, USD Balance: {round(balance, 2)}"
            )
        elif abs(predicted_change) > 0.04:
            balance, btc_balance, model_was_right = execute_trade(
                predicted_price_tomorrow,
                actual_price_today,
                actual_price_tomorrow,
                balance,
                btc_balance,
                implied_values,
            )

            if model_was_right == True:
                model_right_amount += 1
            elif model_was_right == False:
                model_wrong_amount += 1
            # else: the no trade happened

            print(
                f"Trade executed. {ticker} Balance: {round(btc_balance, 5)}, USD Balance: {round(balance, 2)}"
            )

        # Implementing stoploss
        if (
            stoploss_enabled
            and (btc_balance > 0)
            and ((btc_usd_balance_if_ending / initial_balance) <= (1 - stoploss))
        ):
            # print(btc_usd_balance_if_ending / initial_balance, btc_balance, 1 - stoploss)
            balance += btc_balance * actual_price_today
            btc_balance = 0
            print(
                f"Stoploss activated. {ticker} Balance: {round(btc_balance, 6)}, USD Balance: {round(balance, 2)}"
            )
            stoploss = True
            btc_end_override = scaler.inverse_transform(
                np.concatenate(
                    (y_test[i].reshape(-1, 1), np.zeros((1, num_features_backtest))),
                    axis=1,
                )
            )[0, 0]
            break

        btc_usd_balance_if_ending = (btc_balance * actual_price_today) + balance

    change_percent = round(((btc_usd_balance_if_ending / initial_balance) - 1) * 100, 2)

    print()
    print("Backtesting done! Stats:")
    print(f"Initial Balance: ${round(initial_balance, 2)}")
    print(f"Ending balance: ${round(btc_usd_balance_if_ending, 2)}")
    print(f"Total gain/loss: {change_percent}%")
    print(
        f"Out of {trades} trades, {trades_buy} were buys and {trades_sell} were sells"
    )

    print()
    print("--- Buy & Hodl ---")

    btc_start = scaler.inverse_transform(
        np.concatenate(
            (y_test[0].reshape(-1, 1), np.zeros((1, num_features_backtest))), axis=1
        )
    )[0, 0]

    btc_end = 0
    if not btc_end_override:
        btc_end = scaler.inverse_transform(
            np.concatenate(
                (
                    y_test[len(y_test) - 1].reshape(-1, 1),
                    np.zeros((1, num_features_backtest)),
                ),
                axis=1,
            )
        )[0, 0]
    else:
        btc_end = btc_end_override

    gainloss = btc_end / btc_start
    friendly_gainloss_percentage = round((gainloss - 1) * 100, 2)
    is_loss = "gained" if friendly_gainloss_percentage > 0 else "lost"

    is_outperform = (
        "outperformed"
        if change_percent > friendly_gainloss_percentage
        else "underperformed"
    )
    outperform_val = change_percent - friendly_gainloss_percentage

    print(
        f"The market {is_loss} {friendly_gainloss_percentage}% during the test period."
    )
    print(
        f"An investor starting with ${round(initial_balance, 2)} would have ${round(initial_balance * gainloss, 2)} using B&H strategy."
    )

    print(
        f"The model {is_outperform} by {round(outperform_val, 2)}% in comparison to the market."
    )

    print()
    print("EVAL: Copy stats ---")
    print(f"GAINLOSS: {change_percent}")
    print(f"STOPLOSS ACTIVATED: {stoploss_activated}")
    print(f"B&H WINLOSE: {friendly_gainloss_percentage}")
    print(f"OUTPERFORM: {round(outperform_val, 2)}")
    print(f"WINDOW: {window}")
    print(f"LOOKBACK: {lookback}")
    print()
    try:
        print(
            f"The model was right {model_right_amount} times and wrong {model_wrong_amount} times ({round((model_right_amount / (model_right_amount + model_wrong_amount)) * 100, 2)}%)"
        )
    except ZeroDivisionError:
        print(f"Model was right {model_right_amount} times and wrong {model_wrong_amount} times (ZeroDivError)")

    return (
        change_percent,
        stoploss_activated,
        friendly_gainloss_percentage,
        round(outperform_val, 2),
    )
