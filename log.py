import logging

from telegram import Bot


class TelegramLogsHandler(logging.Handler):

    def __init__(self, chat_id, log_bot_token):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = Bot(token=log_bot_token)

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)
