from telegram import Update
from telegram.ext import ContextTypes
from services.gemini_service import GeminiService
from utils.logger import get_logger
import io

logger = get_logger(__name__)

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE, gemini_service: GeminiService):
    """
    Handles incoming voice/audio messages.
    Downloads the audio directly to memory, sends it to Gemini for evaluation/transcription,
    and returns an audio response back.
    """
    chat_id = update.effective_chat.id
    message = update.message or update.channel_post
    
    if not message:
        return
        
    attachment = message.voice or message.audio
    
    if not attachment:
        return

    status_message = await context.bot.send_message(chat_id=chat_id, text="Słucham... (Listening...)")

    try:
        file = await context.bot.get_file(attachment.file_id)
        audio_buffer = io.BytesIO()
        await file.download_to_memory(out=audio_buffer)
        
        audio_bytes = audio_buffer.getvalue()
        mime_type = attachment.mime_type or "audio/ogg"

        logger.info(f"Received audio file ({mime_type}) from user {chat_id}, processing with Gemini...")

        text_response, audio_bytes = gemini_service.handle_audio_search_request(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            play_audio=True, 
            perform_search=False 
        )

        await context.bot.delete_message(chat_id=chat_id, message_id=status_message.message_id)

        if text_response:
            await context.bot.send_message(chat_id=chat_id, text=text_response)
        
        if audio_bytes:
            await context.bot.send_audio(chat_id=chat_id, audio=audio_bytes, filename="audio_tutor.wav")
        elif not text_response:
            await context.bot.send_message(chat_id=chat_id, text="Przepraszam, nie udało mi się przetworzyć Twojej wiadomości.")

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await context.bot.send_message(chat_id=chat_id, text="Przepraszam, wystąpił błąd podczas analizy dźwięku.")
