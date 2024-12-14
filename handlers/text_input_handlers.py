from telegram import Update
from telegram.ext import ContextTypes
from services.gemini_service import GeminiService
from utils.logger import get_logger
from utils.init_environment import Config

BOT_USERNAME = Config().BOT_USERNAME
logger = get_logger(__name__)

async def handle_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE, gemini_service: GeminiService):
    try:
        chat_id = update.effective_chat.id
        text = update.message.text if update.message else update.channel_post.text.strip()

        if text.startswith(f"@{BOT_USERNAME} /ask"):
            user_request = text.split(f"@{BOT_USERNAME} /ask", 1)[1].strip()
            response = gemini_service.fetch_user_request(user_request)

        # Temporary skipped, as it is paid feature for now.
        
        # elif text.startswith(f"@{BOT_USERNAME} /search"):
        #     user_request = text.split(f"@{BOT_USERNAME} /search", 1)[1].strip()
        #     response = gemini_service.fetch_user_search_request(user_request)

        elif text.startswith(f"@{BOT_USERNAME} /repeat"):
            response = gemini_service.fetch_daily_10_words()
        
        # elif text.startswith(f"@{BOT_USERNAME} /news"):
        #     response = gemini_service.fetch_daily_news()
        
        # elif text.startswith(f"@{BOT_USERNAME} /wether"):
        #     response = gemini_service.fetch_daily_weather()
        
        # elif text.startswith(f"@{BOT_USERNAME} /weekly"):
        #     response = gemini_service.fetch_weekly_news()

        elif text.startswith(f"@{BOT_USERNAME} /quiz"):
            response = gemini_service.fetch_daily_quiz()

        elif text.startswith(f"@{BOT_USERNAME} /text"):
            response = gemini_service.fetch_daily_text()

        else:
            response = "Hello, I can respond only for commands I know. They are: /ask, /repeat, /text, /quiz. Also, you could share any image with text with me. Good luck."

        # Send the response back to the user
        await context.bot.send_message(chat_id=chat_id, text=response)

    except Exception as e:
        logger.error(f"Error occurred: {e} during text handler")
        await context.bot.send_message(chat_id=chat_id, text="An error occurred while processing your message.")
