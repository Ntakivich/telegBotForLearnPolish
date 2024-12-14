from telegram import Update
from telegram.ext import ContextTypes
from services.gemini_service import GeminiService
from utils.logger import get_logger
import os

logger = get_logger(__name__)

async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE, gemini_service: GeminiService):
    """
    Handles photo uploads with a text caption mentioning the bot.
    """
    local_path = None  # Initialize local_path to ensure it's always defined
    try:
        message = update.channel_post
        if not message or not message.photo:
            logger.info('no photo is provided')
            return 

        # Ensure there's a caption mentioning the bot
        caption = message.caption or ""
        if f"@{context.bot.username}" not in caption:
            logger.info('bot is not mentioned')
            return 

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
        uploaded_file = gemini_service.upload_file(local_path)
        logger.info(f"Image uploaded to Gemini: {uploaded_file}")

        # Combine image and user prompt for Gemini
        result = gemini_service.model.generate_content([uploaded_file, "\n\n", user_prompt])
        response_text = result.text

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