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
        triggered_function = getattr(gemini_service, triggered_function_name)
        if callable(triggered_function):
            message = triggered_function()
        else:
            raise AttributeError(f"{triggered_function_name} is not callable.")
        
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Message sent at {datetime.now()}: {message}")
    except AttributeError as e:
        logger.error(f"Error: {e} - Method '{triggered_function_name}' not found in GeminiService.")
    except Exception as e:
        logger.error(f"Error posting message: {e}")

async def post_audio(triggered_function_name: str, gemini_service: GeminiService):
    """
    Given a GeminiService method name, execute it to get an audio bytes payload,
    then broadcast it as a voice message to the channel.
    """
    try:
        triggered_function = getattr(gemini_service, triggered_function_name)
        if callable(triggered_function):
            audio_bytes = triggered_function()
        else:
            raise AttributeError(f"{triggered_function_name} is not callable.")
        
        if not audio_bytes:
            logger.error(f"No audio bytes returned by {triggered_function_name}")
            await bot.send_message(chat_id=chat_id, text="Przepraszam, nie udało się wygenerować codziennego dźwięku z powodu przeciążenia serwerów API po stronie Google (błąd 503).")
            return
            
        await bot.send_audio(chat_id=chat_id, audio=audio_bytes, filename="dialog.wav")
        logger.info(f"Audio sent at {datetime.now()} via {triggered_function_name}")
    except AttributeError as e:
        logger.error(f"Error: {e} - Method '{triggered_function_name}' not found in GeminiService.")
    except Exception as e:
        logger.error(f"Error posting audio message: {e}")
