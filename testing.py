# local imports
from src.get_data import *
import src.backtest as backtest
import src.evaluate_model as evaluate_model
import src.process_data as process_data
import src.train_model as train_model
import src.config as config
import src.utils as utils
import src.telegram_bot as telegram

import datetime as dt
import os

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
    layer_neurons,
    layer_delta,
    epochs,
    batchsize,
    target,
    opt_graph,
    opt_backtest,
    parameters,
) = config.get_config()

print(f"EVALUATION MODE: target={target}, parameters={parameters}")
database = {}

acceptable_evaluation_parameters = [
    "layer-neurons",
    "layer-delta",
    "batchsize",
    "window",
    "lookback",
]

if not target in acceptable_evaluation_parameters:
    print(
        "Target is not within acceptable evaluation parameters. Please fix the target field in config.yaml"
    )
    exit(0)


if opt_graph:
    print(
        "Graphing is not available in A/B testing mode. Please run dryrun.py for graphing (overriding user setting)"
    )

if not opt_backtest:
    print("Backtesting is forced in A/B testing mode, overriding user setting.")

opt_graph = False
opt_backtest = True

json = get_data(ticker, coinapi_apikey)
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

telegram_bot = telegram.TelegramBot(telegram_api_key, telegram_password)
telegram_bot.send_message(
    f"✅ Starting A/B backtesting on ticker {ticker}\n(progress will be updated here)..."
)

i = 0
for parameter in parameters:
    print(f"Running A/B test for {target}={parameter}")

    if target == "layer-neurons":
        layer_neurons = parameter
    elif target == "layer-delta":
        layer_delta = parameter
    elif target == "batchsize":
        batchsize = parameter
    elif target == "window":
        window = parameter
    elif target == "lookback":
        lookback = parameter

    i += 1
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

    change_percent, stoploss_activated, gainloss, outperform = (
        evaluate_model.evaluate_model(model, X_test, y_test, scaler, ticker, opt_graph)
    )

    database[parameter] = {
        "change_percent": change_percent,
        "stoploss_activated": stoploss_activated,
        "gainloss": gainloss,
        "outperform": outperform,
    }

    telegram_bot.send_message(
        f"📈 Progress: {ticker}-{target}={parameter} finished - {i}/{len(parameters)} ({round(i / len(parameters), 2)})"
    )

print("A/B Testing Results:")
for parameter in database:
    print(f"Reading out results for {target}={parameter}")
    for subparameter in parameter:
        print(f"{subparameter}: {database[parameter][subparameter]}")

print("A/B Testing Complete. Writing out to results.txt and Telegram")

if os.path.exists("results.txt"):
    os.remove("results.txt")

with open("results.txt", "w") as file:
    file.write("A/B Testing Results:\n")
    for parameter in database:
        file.write(f"Reading out results for {target}={parameter}\n")
        for subparameter in parameter:
            file.write(f"{subparameter}: {database[parameter][subparameter]}\n")

# get results.txt content to write to tg
with open("results.txt", "r") as file:
    results = file.read()

telegram_bot.send_message(
    "A/B Testing Complete:\nResults: \n"
    + results
    + "\n\n✅ A/B Testing Complete. Results written to results.txt."
)
