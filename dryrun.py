# local imports
from get_data import *
import backtest
import evaluate_model
import process_data
import train_model
import config
import utils

# import trade

# no money is involved in this, just training and testing

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
    _,
    _,
    telegram_api_key,
    telegram_password,
) = config.get_config()

# EVALUATION OPTIONS

# OTHER OPTIONS
opt_graph = True
opt_backtest = True

json = get_data(ticker, coinapi_apikey)
# json = load_data(f"{ticker}.json")
json = json[7500:]
# print(len(json))

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
model = train_model.train_model(
    X_train, X_test, y_train, y_test, ticker, model, modelfound
)

num_features, num_features_backtest = evaluate_model.get_num_features()

if opt_backtest:
    backtest.backtest(
        model,
        X_test,
        y_test,
        scaler,
        ticker,
        window,
        lookback,
        num_features,
        num_features_backtest,
    )

evaluate_model.evaluate_model(model, X_test, y_test, scaler, ticker, opt_graph)
