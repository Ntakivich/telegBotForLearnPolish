
from utils.logger import get_logger
from prompts.prompts import prompts
from google import genai
from google.genai import types

logger = get_logger(__name__)


class GeminiService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-pro"
        self.model_for_search = "gemini-2.5-flash"
        self.tutor_model = "gemini-2.5-pro"
        self.chat = self.client.chats.create(
            model=self.tutor_model,
            history=prompts["historySetUP"],
        )

    def upload_file(self, path):
        try:
            return self.client.upload_file(path)
        except Exception as e:
            logger.error(f"Error uploading file to Gemini: {e}")
            return "Error: Could not upload file."
    def fetch_daily_text(self):
        try:
            response = self.chat.send_message(prompts["lerningText"])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching daily text from Gemini: {e}")
            return "Error: Could not retrieve daily text."

    def fetch_daily_quiz(self):
        try:
            response = self.chat.send_message(prompts["learningQuiz"])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching daily quiz from Gemini: {e}")
            return "Error: Could not retrieve daily quiz."

    def fetch_user_request(self, user_request: str):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_request
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching user request from Gemini: {e}")
            return "Error: Could not retrieve user request."

    def fetch_user_search_request(self, user_request: str):
        try:
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(tools=[grounding_tool])
            response = self.client.models.generate_content(
                model=self.model_for_search,
                contents=user_request,
                config=config
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching user search request from Gemini: {e}")
            return "Error: Could not retrieve user search request."

    def fetch_daily_news(self):
        try:
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(tools=[grounding_tool])
            response = self.client.models.generate_content(
                model=self.model_for_search,
                contents=prompts["searchRequestForNews"],
                config=config
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching daily news from Gemini: {e}")
            return "Error: Could not retrieve daily news."

    def fetch_daily_weather(self):
        try:
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(tools=[grounding_tool])
            response = self.client.models.generate_content(
                model=self.model_for_search,
                contents=prompts["searchForWeather"],
                config=config
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching daily weather from Gemini: {e}")
            return "Error: Could not retrieve daily weather."

    def fetch_weekly_news(self):
        try:
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(tools=[grounding_tool])
            response = self.client.models.generate_content(
                model=self.model_for_search,
                contents=prompts["searchWeeklyNews"],
                config=config
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching weekly news from Gemini: {e}")
            return "Error: Could not retrieve weekly news."

    def fetch_daily_10_words(self):
        try:
            response = self.chat.send_message(prompts["learningWords"])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching 10 words from Gemini: {e}")
            return "Error: Could not retrieve 10 words."

    def fetch_daily_words_reminder(self):
        try:
            response = self.chat.send_message(prompts["wordsReminders"])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching reminders from Gemini: {e}")
            return "Error: Could not retrieve reminders."
