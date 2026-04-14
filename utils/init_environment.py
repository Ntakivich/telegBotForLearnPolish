import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)

class AppConfigModel(BaseModel):
    TELEGRAM_BOT_TOKEN: str = Field(..., description="API Token for Telegram Bot")
    TELEGRAM_CHANNEL_ID: int = Field(..., description="Target Channel ID")
    GEMINI_API_KEY: str = Field(..., description="API Key for Google Gemini")
    BOT_USERNAME: str = Field(..., description="Telegram Bot Username (without @)")
    RENDER_EXTERNAL_URL: str | None = None

def _load_env() -> AppConfigModel:
    load_dotenv()
    try:
        config_data = {
            "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
            "TELEGRAM_CHANNEL_ID": os.getenv("TELEGRAM_CHANNEL_ID"),
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "BOT_USERNAME": os.getenv("BOT_USERNAME"),
            "RENDER_EXTERNAL_URL": os.getenv("RENDER_EXTERNAL_URL")
        }
        return AppConfigModel(**config_data)
    except ValidationError as e:
        logger.critical(f"Environment variable validation failed: {e}")
        exit(1)

class Config:
    _instance = None
    _config: AppConfigModel = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._config = _load_env()
        return cls._instance

    def __getattr__(self, name):
        return getattr(self._config, name)
