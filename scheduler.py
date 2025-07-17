from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services import gemini_service
from services.telegram_bot import post_text
from utils.init_environment import Config
from utils.logger import get_logger

logger = get_logger(__name__)

def keep_alive(url: str):
    import requests
    try:
        if url:
            requests.get(url)
            logger.info("Pinged self to keep alive.")
    except Exception as e:
        logger.info(f"Failed to keep alive: {e}")


def setup_scheduler(gemini_service: gemini_service):
    
    async def fetch_daily_words():
      await post_text("fetch_daily_10_words", gemini_service)

    async def fetch_daily_text():
       await post_text("fetch_daily_text", gemini_service)

    async def fetch_daily_quiz():
       await post_text("fetch_daily_quiz", gemini_service)
    
    async def fetch_daily_words_reminder():
       await post_text("fetch_daily_words_reminder", gemini_service)

    async def fetch_daily_news():
        await post_text("fetch_daily_news", gemini_service)

    async def fetch_daily_weather():
        await post_text("fetch_daily_weather", gemini_service)

    async def fetch_weekly_news():
        await post_text("fetch_weekly_news", gemini_service)


    jobs = [
        {"func": fetch_daily_words, "cron": {"hour": 8, "minute": 00}},
        {"func": fetch_daily_text, "cron": {"hour": 14, "minute": 00}},
        {"func": fetch_daily_quiz, "cron": {"hour": 19, "minute": 00}},
        {"func": fetch_daily_words_reminder, "cron": {"hour": 21, "minute": 00}},
        {"func": fetch_daily_news, "cron": {"hour": 12, "minute": 00}},
        {"func": fetch_daily_weather, "cron": {"hour": 7, "minute": 00}},
        {"func": fetch_weekly_news, "cron": {"day_of_week": "mon", "hour": 11, "minute": 00}},
    ]
    scheduler = AsyncIOScheduler()

    for job in jobs:
        scheduler.add_job(job["func"], 'cron', **job["cron"])

    scheduler.add_job(lambda: keep_alive(Config().RENDER_EXTERNAL_URL), 'interval', minutes=10)
    scheduler.start()
