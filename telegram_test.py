# just run the bot and poll

import src.telegram_bot as telegram
import src.config as config

def run_bot(telegram_api_key, telegram_password):
    print("Starting telegram bot (listening for commands)...")
    bot = telegram.TelegramBot(telegram_api_key, telegram_password)
    bot.run()

if __name__ == "__main__":
    settings = config.get_config()
    telegram_api_key = settings[-10]
    telegram_password = settings[-9]
    run_bot(telegram_api_key, telegram_password)