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
    local_path = None
    try:
        message = update.effective_message
        if not message or not message.photo:
            logger.info('no photo is provided')
            return 

        caption = message.caption or ""
        if context.bot.username and f"@{context.bot.username}" not in caption:
            logger.info('bot is not mentioned')
            return 
        file_id = message.photo[-1].file_id
        file = await context.bot.get_file(file_id)
        local_path = f"downloads/{file_id}.jpg"

        os.makedirs("downloads", exist_ok=True)

        await file.download_to_drive(local_path)
        logger.info(f"Photo downloaded to {local_path}")

        user_prompt = caption.replace(f"@{context.bot.username}", "").strip()

        uploaded_file = gemini_service.upload_file(local_path)
        if not uploaded_file:
            raise Exception("Failed to upload image file to Google Gemini API.")
            
        logger.info(f"Image uploaded to Gemini: {uploaded_file}")

        response_text = gemini_service.describe_image(uploaded_file, user_prompt)

        reply_target = update.effective_message
        if reply_target:
            await reply_target.reply_text(response_text)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text)
            
        logger.info(f"Response sent: {response_text}")

    except Exception as e:
        logger.error(f"Error processing photo message: {e}")
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text="Przepraszam, coś poszło nie tak. Spróbuj ponownie.")

    finally:
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Temporary file {local_path} deleted.")