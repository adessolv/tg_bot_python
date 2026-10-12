import logging

from telegram import Update

import config
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from translator import DeeplService
from bot_handlers import start, translate_text, settarget, help, usage, lang_callback

from  flask import Flask, request

import asyncio

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask
app = Flask(__name__)



    # === Создаём Telegram-приложение ===
telegram_app = ApplicationBuilder().token(config.TOKEN).build()

    # === Инициализируем DeepL и сохраняем в контекст ===
telegram_app.bot_data["deepl_service"] = DeeplService(config.DEEPL_AUTH_KEY)

    # === Регистрируем обработчики ===
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help))
telegram_app.add_handler(CommandHandler("settarget", settarget))
telegram_app.add_handler(CommandHandler("usage", usage))

telegram_app.add_handler(CallbackQueryHandler(lang_callback))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))

# --------------------------------------------------------
# ADD ERROR HANDLER  ←← THIS FIXES THE CRASH
# --------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Telegram error: {context.error}")

telegram_app.add_error_handler(error_handler)

# --------------------------------------------------------
# GLOBAL EVENT LOOP (the KEY FIX)
# --------------------------------------------------------
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ===== Webhook
@app.route(f"/{config.TOKEN}", methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, telegram_app.bot)

        loop.run_until_complete(telegram_app.process_update(update))

    except Exception as e:
        logger.error(f"Webhook error: {e}")

    return "OK", 200

@app.route("/")
def index():
    return "Telegram Bot is running", 200

if __name__ == "__main__":
    telegram_app.run_polling(drop_pending_updates=True)