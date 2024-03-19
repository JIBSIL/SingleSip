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
) = config.get_config()

# EVALUATION OPTIONS

# OTHER OPTIONS
opt_graph = False

# set up package based on options
constant_data = (trading_fee, ticker, max_investment, max_trade)

json = get_data(ticker, coinapi_apikey)
json = json[2500:]

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

# if os.path.isfile(model):
#  modelfound = True
# else:
#  modelfound = False

model = train_model.train_model(
    X_train, X_test, y_train, y_test, ticker, model, modelfound
)

num_features, num_features_backtest = evaluate_model.get_num_features()

evaluate_model.evaluate_model(model, X_test, y_test, scaler, ticker, opt_graph)

for _ in range(5):
    print()
print("Starting trading (dryrun DISABLED)")

print(f"\nIntializing trader on pair USDT_{ticker}...")
trader = trade.Trader("USDC", ticker, poloniex_api_key, poloniex_secret)
print("Trader initialized!\n")

# initialize predictor
predictor = prediction.Predictor(
    ticker, lookback, coinapi_apikey, model, trader, constant_data
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
