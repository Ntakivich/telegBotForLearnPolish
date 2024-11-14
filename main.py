import os
import logging
import threading
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import requests

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
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Start a persistent chat session
chat = model.start_chat(history=[
    {"role": "user", "parts": "Imagine that you are a super expert Polish teacher, who is working with B1 students and specifically focusing on conversational skills. Always responds in Polish and additionaly always ads 1 popular conversation phrase to each response."},
    {"role": "model", "parts": "Oczywiście! Jak mogę Ci dziś pomóc w nauce języka polskiego? 😊Popularna fraza: "'Co słychać?'" - używane, aby zapytać, co u kogoś nowego."}
])

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Send response status code
        self.send_response(200)
        
        # Set headers
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Write message
        self.wfile.write(b"Hello, visitor!")

def keep_alive():
    try:
        url = os.getenv("RENDER_EXTERNAL_URL")
        if url:
            requests.get(url)
            print("Pinged self to keep alive.")
    except Exception as e:
        print(f"Failed to keep alive: {e}")

def start_http_server():
    # Start a simple HTTP server to listen on the required port
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"HTTP server running on port {port}")
    server.serve_forever()
    
def fetch_daily_10_words():
    """
    Fetch a daily learning message with words within the persistent chat session to retain context.
    """
    try:
        response = chat.send_message("Please provide 10 B1 Polish words with context and examples, definitely not repeat yourself and answer in Polish.")
        message_content = response.text.strip()
        return message_content
    except Exception as e:
        logger.error(f"Error fetching message from Gemini: {e}")
        return "Error: Could not retrieve message."

def fetch_daily_text():
    """
    Fetch a daily learning message with text within the persistent chat session to retain context.
    """
    try:
        response = chat.send_message("Please, provide medium size text (~20 sentences) B1 level, highlight not obvious words for such level and explain them separately with additional context. Respond only in Polish and don't repeat yourself when i ask this again.")
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

async def post_10_words():
    """
    Fetches a message with 10 words from the persistent chat session and posts it to the Telegram channel.
    """
    message = fetch_daily_10_words()
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
        logger.info(f"Message sent at {datetime.now()}: {message}")
    except Exception as e:
        logger.error(f"Error posting message: {e}")


async def post_learning_text():
    """
    Fetches a message with learning text from the persistent chat session and posts it to the Telegram channel.
    """
    message = fetch_daily_text()
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
    daily_message_repeat = fetch_daily_10_words()

    await context.bot.send_message(chat_id=chat_id, text=daily_message_repeat)
    logger.info(f"Responded to /repeat command in {update.effective_chat.type}: {daily_message_repeat}")

async def handle_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the '/text' command to fetch and post the daily message.
    """
    chat_id = update.effective_chat.id
    daily_text = fetch_daily_text()

    await context.bot.send_message(chat_id=chat_id, text=daily_text)
    logger.info(f"Responded to /text command in {update.effective_chat.type}: {daily_text}")

async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles photo uploads with a text caption mentioning the bot.
    """
    local_path = None  # Initialize local_path to ensure it's always defined
    try:
        message = update.channel_post
        if not message or not message.photo:
            logger.info('no photo is provided')
            return  # Exit if no photo is provided

        # Ensure there's a caption mentioning the bot
        caption = message.caption or ""
        if f"@{context.bot.username}" not in caption:
            logger.info('bot is not mentioned')
            return  # Exit if bot is not mentioned

        # Extract the photo (highest resolution is the last one in the list)
        file_id = message.photo[-1].file_id
        file = await context.bot.get_file(file_id)
        local_path = f"downloads/{file_id}.jpg"

        # Ensure the downloads directory exists
        os.makedirs("downloads", exist_ok=True)

        # Download the photo locally
        await file.download_to_drive(local_path)
        logger.info(f"Photo downloaded to {local_path}")

        # Extract the user prompt from the caption
        user_prompt = caption.replace(f"@{context.bot.username}", "").strip()

        # Upload the image to Gemini
        uploaded_file = genai.upload_file(local_path)
        logger.info(f"Image uploaded to Gemini: {uploaded_file}")

        # Combine image and user prompt for Gemini
        result = model.generate_content([uploaded_file, "\n\n", user_prompt])
        response_text = result.text

        # Respond in the Telegram chat
        await message.reply_text(response_text)
        logger.info(f"Response sent: {response_text}")

    except Exception as e:
        logger.error(f"Error processing photo message: {e}")
        await update.message.reply_text("Sorry, something went wrong. Please try again.")

    finally:
        # Cleanup the downloaded file if it exists
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Temporary file {local_path} deleted.")


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
            response = f"I'm here to help! Use commands like /ask or /repeat /text. Type @{BOT_USERNAME} /ask and then ask anything you want without context, one time response. Type  @{BOT_USERNAME} /repeat to repeat polish 10 words. Type  @{BOT_USERNAME} /text to repeat learning Polish text. Post image and tag @{BOT_USERNAME} with question to receive response based on photo."
            await context.bot.send_message(chat_id=chat_id, text=response)
            logger.info(f"Responded to mention in {message_type}")
    except Exception as e:
        logger.error(f"Error handling general message: {e}")

def main():
    # Initialize the bot application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    # Initialize the server for self ping
    http_thread = threading.Thread(target=start_http_server)
    http_thread.start()

    # Add command handlers
    ask_handler = MessageHandler(filters.TEXT & filters.Regex(f"@{BOT_USERNAME} /ask"), handle_ask_command)
    repeat_handler = MessageHandler(filters.TEXT & filters.Regex(f"@{BOT_USERNAME} /repeat"), handle_repeat_command)
    learning_text_handler = MessageHandler(filters.TEXT & filters.Regex(f"@{BOT_USERNAME} /text"), handle_text_command)
    photo_handler = MessageHandler(filters.PHOTO & filters.CaptionRegex(f"@{BOT_USERNAME}"), handle_photo_message)
    application.add_handler(ask_handler)
    application.add_handler(repeat_handler)
    application.add_handler(learning_text_handler)
    application.add_handler(photo_handler)

    # Add handler for general messages (optional, for logging or responding to mentions)
    general_message_handler = MessageHandler(filters.ALL, handle_general_message)
    application.add_handler(general_message_handler)

    # Scheduler setup using AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(post_10_words, 'cron', hour=12, minute=00)
    scheduler.add_job(post_learning_text, 'cron', hour=17, minute=00)
    scheduler.add_job(keep_alive, "interval", minutes=10)
    scheduler.start()

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    os.makedirs("downloads", exist_ok=True)
    main()