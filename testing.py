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
import signal
import shutil

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
json = json[7500:] # remove last 7500 parts of data

# before we get started, clean up from previous runs
utils.cleanup_last_generation()

df_merged = process_data.process_data(json)
df_scaled, scaler = process_data.add_technical_indicators(
    df_merged, window, traintest_split
)
X_train, X_test, y_train, y_test = process_data.prepare_training_dataset(
    df_scaled, lookback, traintest_split
)

telegram_bot, thread = telegram.run_bot(telegram_api_key, telegram_password)

telegram_bot.send_message(
    f"✅ Starting A/B backtesting on ticker {ticker}\n(progress will be updated here)..."
)

# delete models/eval
if os.path.exists("models/eval"):
    shutil.rmtree("models/eval")

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
    # modelfound = False if model != None else True
    modelfound = (
        True  # set this to true to force training of new model (it's a bit backwards)
    )
    formatted_date = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    training_data = (
        layer_neurons,
        layer_delta,
        epochs,
        batchsize,
        f"models/eval/evaluation_{ticker}_{target}={parameter}_{formatted_date}",
    )

    model = train_model.train_model(
        X_train,
        X_test,
        y_train,
        y_test,
        ticker,
        f"models/eval/evaluation_{ticker}_{target}={parameter}_{formatted_date}.zip",
        modelfound,
        training_data,
    )

    num_features, num_features_backtest = evaluate_model.get_num_features()

    if opt_backtest:
        change_percent, stoploss_activated, gainloss, outperform = backtest.backtest(
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

    database[parameter] = {
        "change_percent": change_percent,
        "stoploss_activated": stoploss_activated,
        "gainloss": gainloss,
        "outperform": outperform,
    }
    
    msg = (f"📈 Progress: {ticker}-{target}={parameter} finished - {i}/{len(parameters)} ({round(100 * (i / len(parameters)), 2)}%)\n" +
        f"Outperform: {outperform}\n" +
        f"Stoploss Activated: {stoploss_activated}\n")
    
    if change_percent == 0.0:
        msg += "ZeroDivError - model errored and made no trades"
    
    telegram_bot.send_message(msg)

print("A/B Testing Results:")
for parameter in database:
    print(f"Reading out results for {target}={parameter}")
    for subparameter in database[parameter]:
        print(f"{subparameter}: {database[parameter][subparameter]}")

print("A/B Testing Complete. Writing out to results.txt and Telegram")

if os.path.exists("results.txt"):
    os.remove("results.txt")

msg_telegram = "A/B Testing Results:\n\n"

with open("results.txt", "w") as file:
    for parameter in database:
        title = f"Results for {target}={parameter}:"
        msg_telegram += f"**{title}**\n"
        file.write(f"{title}\n")
        for subparameter in database[parameter]:
            sanitized_param = subparameter.replace("_", "-")
            subparam = f"{sanitized_param}: {database[parameter][subparameter]}\n"
            msg_telegram += subparam
            file.write(subparam)
        file.write("\n")
        msg_telegram += "\n"

telegram_bot.send_message(
    msg_telegram +
    "\n✅ A/B Testing Complete. Results written to results.txt."
)

os.kill(os.getpid(), signal.SIGTERM)