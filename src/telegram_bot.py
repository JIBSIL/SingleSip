# pip install python-telegram-bot

import time
import os
import threading
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

if __name__ == "__main__":
    import src.config as config


class TelegramDatastore:
    def __init__(self):
        self.authenticated_users = []
        self.read_database()

    def write_out(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if os.path.exists("data/telegram_authentication.txt"):
            os.remove("data/telegram_authentication.txt")
        with open("data/telegram_authentication.txt", "w") as file:
            for user in self.authenticated_users:
                file.write(f"{user}\n")

    def read_database(self):
        if not os.path.exists("data/telegram_authentication.txt"):
            return
        with open("data/telegram_authentication.txt", "r") as file:
            for line in file:
                self.authenticated_users.append(int(line.strip()))

    def authenticate(self, user_id):
        self.authenticated_users.append(user_id)
        self.write_out()

    def is_authenticated(self, user_id):
        return user_id in self.authenticated_users


class TelegramBot:
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.database.is_authenticated(context._user_id):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="SingleSip AlgoTrade Communicator. Please /authenticate.",
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="SingleSip AlgoTrade Communicator. You are authenticated.",
            )

    async def authenticate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.database.is_authenticated(context._user_id):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You are already authenticated.",
            )
            return
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Hello user {context._user_id}. Please enter the system password to authenticate.",
        )
        self.temporary_userstates[context._user_id] = "awaiting_password"

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context._user_id not in self.temporary_userstates:
            return
        if self.temporary_userstates[context._user_id] == "awaiting_password":
            if update.message.text.lower() == "cancel":
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Authentication cancelled.",
                )
                del self.temporary_userstates[context._user_id]
                return
            if update.message.text == self.password:
                self.database.authenticate(context._user_id)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="You are now authenticated.",
                )
                del self.temporary_userstates[context._user_id]
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text='Incorrect password. Please try again or type "cancel".',
                )

    async def send_message(self, message):
        for user_id in self.database.authenticated_users:
            await self.bot.send_message(chat_id=user_id, text=message)

    def __init__(self, token, password):
        self.token = token
        self.bot = ApplicationBuilder().token(token).build()
        self.password = password
        self.database = TelegramDatastore()
        self.temporary_userstates = {}

        start_handler = CommandHandler("start", self.start)
        authentication_handler = CommandHandler("authenticate", self.authenticate)
        message_handler = MessageHandler(
            filters.TEXT & (~filters.COMMAND), self.message_handler
        )

        self.bot.add_handler(start_handler)
        self.bot.add_handler(authentication_handler)
        self.bot.add_handler(message_handler)
        thread = threading.Thread(target=self.run, args=[])
        thread.start()

    def run(self):
        self.bot.run_polling()


if __name__ == "__main__":
    settings = config.get_config()
    telegram_api_key = settings[-2]
    telegram_password = settings[-1]
    print("Starting telegram bot (listening for commands)...")
    TelegramBot(telegram_api_key, telegram_password)
