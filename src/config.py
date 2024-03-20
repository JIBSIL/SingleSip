import yaml
import os


def get_config():
    # OPTIONS
    ticker = "LTC"
    window = 14
    lookback = 14
    model = (
        None  # if Tensorflow export zipfile is set, it will be used instead of training
    )
    coinapi_apikey = ""
    traintest_split = 0.2

    # TRADING OPTIONS
    max_investment = 1000000  # basically disabled
    max_trade = 0.4  # 40% of the balance
    # trading_fee = 0.001015 # 0.25%
    trading_fee = 0.002
    poloniex_api_key = ""
    poloniex_secret = ""

    # TELEGRAM BOT OPTIONS
    telegram_api_key = ""
    telegram_password = ""

    # TRAINING OPTIONS
    layer_neurons = 175
    layer_delta = 25
    epochs = 100
    batchsize = 64

    # TESTING OPTIONS
    target = ""
    parameters = []
    opt_graph = False
    opt_backtest = False

    # test if config.yaml exists

    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)
            ticker = config["ticker"]
            window = config["window"]
            lookback = config["lookback"]
            model = config["model"]
            coinapi_apikey = config["coinapi-apikey"]
            traintest_split = config["traintest-split"]

            max_investment = config["trading-options"]["max-investment"]
            max_trade = config["trading-options"]["max-trade"]
            trading_fee = config["trading-options"]["trading-fee"]
            poloniex_api_key = config["trading-options"]["poloniex-api-key"]
            poloniex_secret = config["trading-options"]["poloniex-secret"]

            telegram_api_key = config["communication-options"]["telegram-api-key"]
            telegram_password = config["communication-options"]["telegram-password"]

            telegram_api_key = config["communication-options"]["telegram-api-key"]
            telegram_password = config["communication-options"]["telegram-password"]

            layer_neurons = config["training-options"]["layer-neurons"]
            layer_delta = config["training-options"]["layer-delta"]
            epochs = config["training-options"]["epochs"]
            batchsize = config["training-options"]["batchsize"]

            target = config["testing-options"]["target"]
            parameters = config["testing-options"]["parameters"]
            opt_graph = config["testing-options"]["graph"]
            opt_backtest = config["testing-options"]["backtest"]

            return (
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
            )
    else:
        print("config.yaml not found, using defaults")
        config = {
            "ticker": ticker,
            "window": window,
            "lookback": lookback,
            "model": model,
            "coinapi-apikey": coinapi_apikey,
            "traintest-split": traintest_split,
            "trading-options": {
                "max-investment": max_investment,
                "max-trade": max_trade,
                "trading-fee": trading_fee,
                "poloniex-api-key": poloniex_api_key,
                "poloniex-secret": poloniex_secret,
            },
            "communication-options": {
                "telegram-api-key": telegram_api_key,
                "telegram-password": telegram_password,
            },
            "training-options": {
                "layer-neurons": layer_neurons,
                "layer-delta": layer_delta,
                "epochs": epochs,
                "batchsize": batchsize,
            },
            "testing-options": {
                "target": target,
                "parameters": parameters,
                "graph": opt_graph,
                "backtest": opt_backtest,
            },
        }

        yaml.dump(config, open("config.yaml", "w"))

        print(
            f"config.yaml created with default values. Please fill in the required fields and run again."
        )
        exit(0)
