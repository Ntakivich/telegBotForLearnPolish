import os
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger(__name__)

class Config:
    def __init__(self):
        load_dotenv()
        required_env_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID", "GEMINI_API_KEY", "BOT_USERNAME"]
        for var in required_env_vars:
            if not os.getenv(var):
                logger.critical(f"Environment variable {var} is missing.")
                exit(1)
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.TELEGRAM_CHANNEL_ID = int(os.getenv("TELEGRAM_CHANNEL_ID"))
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.BOT_USERNAME = os.getenv("BOT_USERNAME")
        self.RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
