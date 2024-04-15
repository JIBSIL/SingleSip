# local imports
from src.get_data import *
import src.backtest as backtest
import src.evaluate_model as evaluate_model
import src.process_data as process_data
import src.train_model as train_model
import src.config as config
import src.utils as utils

import datetime as dt

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
    tests
) = config.get_config()

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

if tests["lightning"]:
    if lookback != 1:
        print("Lookback must be 1 for pytorch-lightning. Setting lookback to 1...")
    lookback = 1

X_train, X_test, y_train, y_test = process_data.prepare_training_dataset(
    df_scaled, lookback, traintest_split
)

if tests["lightning"]:
    import src.tests.lightning_trainer as lightning
    
    features = process_data.get_features()
    
    feature_x_dim = features["features"]
    feature_x_dim.append("IDX")

    X_train_df = pd.DataFrame(X_train.reshape(X_train.shape[0], -1), columns=feature_x_dim)
    y_train_df = pd.DataFrame(y_train, columns=features["target"])
    
    train_df = pd.concat([y_train_df, X_train_df], axis=1)
    train_df["IDX"] = range(0, len(train_df))
    #print(train_df.head())
    
    model, dset_val = lightning.prepare_and_train(train_df, model)
    #exit(0)
else:
    modelfound = False if model != None else True
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

if opt_backtest:
    if tests["lightning"]:
        import src.tests.lightning_backtest as lightning_backtest
        
        num_features, num_features_backtest = evaluate_model.get_num_features()
        lightning_backtest.backtest(
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
    else:
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
