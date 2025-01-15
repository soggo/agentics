from typing import Final
from telebot import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


TOKEN: Final = "6723409693:AAFNJRzcsfHSYt7zcYIXpd07BuXN2baavZA"
BOT_USERNAME: Final = "@namecostbot"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text()