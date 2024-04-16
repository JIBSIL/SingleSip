## Configuration

Outlined here are all of the configuration settings in this project.

`ticker`: string; ticker for CoinAPI - e.g LTC or BTC

`window`: number; the window of time (organized into four-hour steps) that the model considers at one time while predicting

`lookback`: number; amount of steps to consider for technical indicators

`model`: string; relative or absolute path to a model. Lightning .ckpt models are supported, as well as zipped Tensorflow/Keras .zip models

`coinapi-apikey`: string; API key for [CoinAPI](https://www.coinapi.io/)

`traintest-split`: float; split between training and testing data. Should be a float specifying the amount of testing data to use, out of 1. For example, 0.1 would indicate that 90% of training data should be used, and 10% should be used for testing.

`communication-options`: telegram options
- `telegram-api-key`: string; bot API key from Telegram's bot maker `BotFather`
- `telegram-password`: string; password used to authenticate with your Telegram bot

`trading-options`: live trading and backtest options
- `max-investment`: integer; maximum amount in coins/dollars to trade at one time (recommended to set to 100000000000 to effectively disable it, as setting max-trade is more effective)
- `max-trade`: float; % amount to trade at one time, as a float. For example, 0.2 would trade 20% of the funds in a certain side of the pair at a time
- `trading-fee`: float; trading fee per trade, out of 1. For example, 0.01 would be a 1% fee per trade.
- `poloniex-api-key`: string; API key for poloniex
- `poloniex-secret`: string; Poloniex secret key

`training-options`: options used for training
- `layer-neurons`: number; amount of neurons in a certain layer. Recommended values range from 50-250
- `layer-delta`: number; amount of neurons to decrease by, per layer. Recommended values range from 5-50
- `epochs`: number; amount of epochs to train for. This may not be reached because of early stopping when the validation loss is low enough.
- `batchsize`: number; amount of datapoints to pass to the model at once. Higher batchsizes make the model train faster, but can decrease financial performance.

`testing-options`: options for A/B testing
- `target`: string; any option in `training-options`, for example, `layer-neurons`
- `parameters`: array; parameters to manipulate the `target` with, as an array. For example, [100, 75, 50, 25] to test those values of `target`
- `graph`: boolean; whether to graph the coorelation between predicted and actual performance.
- `backtest`: boolean; whether to simulate training using the integrated backtest software

`tests`: experimental options
- `lightning`: boolean; whether to enable PyTorch Lightning. This is only useful for training models, as backtesting and trading are not implemented yet.