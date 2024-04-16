## SingleSip

SingleSip: open-source and free next-gen trading bot for hundreds of cryptocurrencies. Integrated backtesting, data acquisition, evaluation, A/B testing and trading.

## Intro
SingleSip is organized into backtesting, A/B testing and evaluation. Some Python, Tensorflow and finance experience is required to get the most out of the project. If you have the required knowledge and spend some time adjusting settings, the model should work well. That being said, this project is **not plug-and-play**, due to the complexity of the technologies used and the dynamic nature of financial markets.

## Setting up
The setup is somewhat complicated. You will want to sign up for CoinAPI and Poloniex, as well as create a Telegram bot for live info on trading and testing. Next, follow these steps:
1. Create a new Conda environment with Python 3.10.14. I personally recommend using [Miniconda](https://docs.anaconda.com/free/miniconda/index.html)
2. Run `pip install -r requirements.txt` in the main folder
3. Create the configuration file by running `python dryrun.py`
4. Explore and populate the configuration values. They are documented in [CONFIG.md](CONFIG.md)
5. Run `dryrun.py` again to train your model. The model should be in the `models` folder
6. Change the `model` configuration setting in `config.yaml` to the model path that you just trained on
7. Run `evaluation.py` to determine if the model is profitable on average. If it is not, consider adjusting settings in `config.yaml` until it is.
8. Run `run.py` to start trading. You will have to run `/start` on the Telegram bot and authenticate for live trading updates.

## Project files
- `telegram_test.py` - Probably not needed for most use cases - you can test if the Telegram bot is working by running this file
- `evaluation.py` - Used to evaluate a singular model and find the average profit and outperform statistics for a selected model
- `dryrun.py` - Used to backtest and train a singular model
- `testing.py` - Used for A/B testing. Comes with an integration with Telegram
- `run.py` - Used for live trading. Comes with an integration with Telegram

## Third Party Software
Several technologies were used in the making of this project. Here is a non-exaustive list of the major ones:
- [polosdk](https://github.com/poloniex/polo-sdk-python) - Poloniex SDK
- Tensorflow - Used to train the models
- python-telegram-bot - Wrapper for Telegram, used for the integration with trading
- PyTorch Lightning - An integration with PyTorch Lightning (via pytorch_forecasting) is still in development

## Bugs
If you would like to report a bug, feel free to report it in [our Issues tracker](https://github.com/JIBSIL/SingleSip/issues). 

## Integration with your business
If you are looking for specific help with your integration of SingleSip, please contact me through the contacts on [my profile](https://github.com/JIBSIL).