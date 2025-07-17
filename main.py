import threading
from services.gemini_service import GeminiService
from handlers.image_handler import handle_photo_message
from handlers.text_input_handlers import handle_text_command
from scheduler import setup_scheduler
from utils.init_environment import Config
from server import start_http_server
from telegram.ext import Application, MessageHandler, filters
import os
from telegram.ext import Application
from utils.logger import setup_logger, get_logger

config = Config()

setup_logger()
logger = get_logger(__name__)

def main():

    http_thread = threading.Thread(target=start_http_server)
    http_thread.start()
    logger.info('Server started')

    gemini_service = GeminiService(
        api_key=config.GEMINI_API_KEY
    )
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    logger.info('Bot started')


    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(f"@{config.BOT_USERNAME}"), lambda update, context: handle_text_command(update, context, gemini_service)))
    application.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(f"@{config.BOT_USERNAME}"), lambda update, context: handle_photo_message(update, context, gemini_service)))
    logger.info('Handlers started')


    async def on_startup(app):
        await setup_scheduler(gemini_service)
        logger.info('Scheduler started')

    application.post_init = on_startup
    application.run_polling()
    logger.info('Polling in process...')

if __name__ == '__main__':
    os.makedirs("downloads", exist_ok=True)
    main()