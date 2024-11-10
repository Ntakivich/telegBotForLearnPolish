import os
import logging
import threading
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from http.server import SimpleHTTPRequestHandler, HTTPServer
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables for sensitive data
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
BOT_USERNAME = os.getenv('BOT_USERNAME') 

# Initialize Gemini and Telegram bot
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Start a persistent chat session
chat = model.start_chat(history=[
    {"role": "user", "parts": "Please imagine that you are a super expert Polish teacher."},
    {"role": "model", "parts": "Got it! As your expert Polish teacher, I'm here to help with anything from grammar to conversation practice. How would you like to start? Would you prefer to dive into vocabulary, pronunciation, or perhaps grammar basics?"}
])

def start_http_server():
    # Start a simple HTTP server to listen on the required port
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"HTTP server running on port {port}")
    server.serve_forever()
    
def fetch_daily_message():
    """
    Fetch a daily message within the persistent chat session to retain context.
    """
    try:
        response = chat.send_message("Please, provide 10 popular words in Polish (intermediate level) with context and explanation.")
        message_content = response.text.strip()
        return message_content
    except Exception as e:
        logger.error(f"Error fetching message from Gemini: {e}")
        return "Error: Could not retrieve message."

def fetch_user_ask_request(user_request):
    """
    Fetch user request message.
    """
    try:
        response = model.generate_content(user_request)
        message_content = response.text.strip()
        return message_content
    except Exception as e:
        logger.error(f"Error fetching message from Gemini: {e}")
        return "Error: Could not retrieve message."

async def post_message():
    """
    Fetches a message from the persistent chat session and posts it to the Telegram channel.
    """
    message = fetch_daily_message()
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
        logger.info(f"Message sent at {datetime.now()}: {message}")
    except Exception as e:
        logger.error(f"Error posting message: {e}")

async def handle_ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the '/ask' command with the bot username to fetch and post a response.
    """
    chat_id = update.effective_chat.id
    text = update.message.text if update.message else update.channel_post.text

    # Extract user request after the /ask command
    user_request = text.split(f"@{BOT_USERNAME} /ask", 1)[1].strip()
    response = fetch_user_ask_request(user_request)

    await context.bot.send_message(chat_id=chat_id, text=response)
    logger.info(f"Responded to /ask request in {update.effective_chat.type}: {response}")

async def handle_repeat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the '/repeat' command to fetch and post the daily message.
    """
    chat_id = update.effective_chat.id
    daily_message_repeat = fetch_daily_message()

    await context.bot.send_message(chat_id=chat_id, text=daily_message_repeat)
    logger.info(f"Responded to /repeat command in {update.effective_chat.type}: {daily_message_repeat}")

async def handle_general_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    General message handler to log messages and respond if necessary.
    """
    try:
        chat = update.effective_chat
        text = update.message.text if update.message else update.channel_post.text
        message_type = chat.type
        chat_id = chat.id

        # Log the received message
        logger.info(f'User ({chat_id}) in {message_type}: "{text}"')

        # If the bot is mentioned, it will respond with a default message
        if BOT_USERNAME and f"@{BOT_USERNAME}" in text:
            response = f"I'm here to help! Use commands like /ask or /repeat. Type @{BOT_USERNAME} /ask and then ask anything you want without context, one time response. Type  @{BOT_USERNAME} /repeat to repeat polish 10 words"
            await context.bot.send_message(chat_id=chat_id, text=response)
            logger.info(f"Responded to mention in {message_type}")
    except Exception as e:
        logger.error(f"Error handling general message: {e}")

def main():
    # Initialize the bot application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    http_thread = threading.Thread(target=start_http_server)
    http_thread.start()

    # Add command handlers for '/ask' and '/repeat' commands
    ask_handler = MessageHandler(filters.TEXT & filters.Regex(f"@{BOT_USERNAME} /ask"), handle_ask_command)
    repeat_handler = MessageHandler(filters.TEXT & filters.Regex(f"@{BOT_USERNAME} /repeat"), handle_repeat_command)
    application.add_handler(ask_handler)
    application.add_handler(repeat_handler)

    # Add handler for general messages (optional, for logging or responding to mentions)
    general_message_handler = MessageHandler(filters.ALL, handle_general_message)
    application.add_handler(general_message_handler)

    # Scheduler setup using AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(post_message, 'cron', hour=12, minute=00)
    scheduler.start()

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()