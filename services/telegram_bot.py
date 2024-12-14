from telegram import Bot
from services.gemini_service import GeminiService
from utils.logger import get_logger
from datetime import datetime
from utils.init_environment import Config

config = Config()

bot = Bot(config.TELEGRAM_BOT_TOKEN)
chat_id = config.TELEGRAM_CHANNEL_ID
logger = get_logger(__name__)

async def post_text(triggered_function_name: str, gemini_service: GeminiService):
    try:
        # Dynamically retrieve and call the specified method
        triggered_function = getattr(gemini_service, triggered_function_name)
        if callable(triggered_function):
            message = triggered_function()
        else:
            raise AttributeError(f"{triggered_function_name} is not callable.")
        
        # Send the message to the Telegram channel
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Message sent at {datetime.now()}: {message}")
    except AttributeError as e:
        logger.error(f"Error: {e} - Method '{triggered_function_name}' not found in GeminiService.")
    except Exception as e:
        logger.error(f"Error posting message: {e}")
