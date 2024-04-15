# local imports

from scheduler import Scheduler
import datetime as dt
import time
import os

from src.get_data import *
import src.prediction as prediction
import src.evaluate_model as evaluate_model
import src.process_data as process_data
import src.train_model as train_model
import src.trade as trade
import src.config as config
import src.utils as utils
import src.telegram_bot as telegram

(
    ticker,
    window,
    lookback,
    model,
    coinapi_apikey,
    traintest_split,
    max_investment,
    max_trade,
    trading_fee,
    poloniex_api_key,
    poloniex_secret,
    telegram_api_key,
    telegram_password,
    layer_neurons,
    layer_delta,
    epochs,
    batchsize,
    target,
    opt_graph,
    opt_backtest,
    parameters,
    tests
) = config.get_config()

if opt_backtest == True:
    print(
        "Backtesting is not available in the live version of SingleSip. Please run dryrun.py for backtesting."
    )

# EVALUATION OPTIONS

# set up package based on options
constant_data = (trading_fee, ticker, max_investment, max_trade)

json = get_data(ticker, coinapi_apikey)
json = json[7500:]

# before we get started, clean up from previous runs
utils.cleanup_last_generation()

df_merged = process_data.process_data(json)
df_scaled, scaler = process_data.add_technical_indicators(
    df_merged, window, traintest_split
)
X_train, X_test, y_train, y_test = process_data.prepare_training_dataset(
    df_scaled, lookback, traintest_split
)

modelfound = False if model != None else True

formatted_date = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
training_data = (
    layer_neurons,
    layer_delta,
    epochs,
    batchsize,
    "models/evaluation_{ticker}_{formatted_date}.zip",
)

model = train_model.train_model(
    X_train, X_test, y_train, y_test, ticker, model, modelfound, training_data
)

num_features, num_features_backtest = evaluate_model.get_num_features()

evaluate_model.evaluate_model(model, X_test, y_test, scaler, ticker, opt_graph)

for _ in range(5):
    print()
print("Starting trading (dryrun DISABLED)")

print(f"\nIntializing trader on pair USDC_{ticker}...")
trader = trade.Trader("USDC", ticker, poloniex_api_key, poloniex_secret)
print("Trader initialized!\n")

telegram_bot, thread = telegram.run_bot(telegram_api_key, telegram_password)

telegram_bot.send_message(
    f"✅ Starting realtime trading on ticker USDT_{ticker} (dryrun off)..."
)

# initialize predictor
predictor = prediction.Predictor(
    ticker, lookback, coinapi_apikey, model, trader, constant_data, telegram_bot
)


def trade_periodic():
    print("Making new trade...")
    predictor.trade()


print()
print("Printing schedule")
schedule = Scheduler()
schedule.cyclic(dt.timedelta(hours=4), trade_periodic)

print(schedule)

balances = trader.get_balances()
print(f"USD Balance: {balances[0]}\n{ticker} Balance: {balances[1]}")

while True:
    schedule.exec_jobs()
    time.sleep(1)
