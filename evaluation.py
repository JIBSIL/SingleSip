# local imports
from src.get_data import *
import src.backtest as backtest
import src.evaluate_model as evaluate_model
import src.process_data as process_data
import src.train_model as train_model
import src.config as config
import src.utils as utils

import datetime as dt
import numpy as np

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
    _,
    _,
    layer_neurons,
    layer_delta,
    epochs,
    batchsize,
    target,
    opt_graph,
    opt_backtest,
    parameters,
) = config.get_config()

if model == "":
    print('Evaluation.py does not support training a new model. Use dryrun.py for this purpose.')
    exit(0)

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
    df_scaled, lookback, traintest_split, shuffle=True
)

modelfound = False
formatted_date = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
training_data = (
    layer_neurons,
    layer_delta,
    epochs,
    batchsize,
    f"models/evaluation_{ticker}_{formatted_date}.zip",
)

model = train_model.train_model(
    X_train, X_test, y_train, y_test, ticker, model, modelfound, training_data
)

num_features, num_features_backtest = evaluate_model.get_num_features()

if not opt_backtest:
    print('Backtesting is disabled but we are running in eval mode. Overriding..')

change_percents = []
outperforms = []
stoploss_activated_times = 0

for i in range(10):
    X_train, X_test, y_train, y_test = process_data.prepare_training_dataset(
        df_scaled, lookback, traintest_split, shuffle=True
    )
    
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
    
    if stoploss_activated:
        stoploss_activated_times += 1
    
    change_percents.append(change_percent)
    outperforms.append(outperform)

evaluate_model.evaluate_model(model, X_test, y_test, scaler, ticker, opt_graph)

# calculate std deviation
print('EVALUATION RESULTS')
print(f'Stoploss activated {stoploss_activated_times} times')
print('Average outperform is', np.mean(outperforms))
print('Median outperform is', np.median(outperforms))
print('Standard deviation for change percents is', np.std(change_percents))
print('Standard deviation for outperform is', np.std(outperforms))
print()
print('Variance for outperform is', np.var(outperforms))
print('Variance for change percents is', np.var(change_percents))