from utils.logger import get_logger
from prompts.prompts import prompts
import google.generativeai as genai

logger = get_logger(__name__)

class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
        
        # Temporary skipped, as it is paid feature for now.
        # self.model_for_search = genai.GenerativeModel("gemini-2.0-flash-exp")

        self.tutor_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-04-17",
            system_instruction=(
                prompts["systemInstructions"]
            )
        )
        self.chat = self.tutor_model.start_chat(history=prompts["historySetUP"])

    def upload_file(self, path):
        try:
            return  genai.upload_file(path)
        except Exception as e:
            logger.error(f"Error uploading file to Gemini: {e}")
            return "Error: Could not upload file."
    def fetch_daily_text(self):
        try:
            response = self.chat.send_message(
                prompts["lerningText"]
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching daily text from Gemini: {e}")
            return "Error: Could not retrieve daily text."

    def fetch_daily_quiz(self):
        try:
            response = self.chat.send_message(
                prompts["learningQuiz"]
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching daily quiz from Gemini: {e}")
            return "Error: Could not retrieve daily quiz."

    def fetch_user_request(self, user_request: str):
        try:
            response = self.model.generate_content(user_request)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching user request from Gemini: {e}")
            return "Error: Could not retrieve user request."
    # Temporary skipped, as it is paid feature for now.
    # def fetch_user_search_request(self, user_request: str):
    #     try:
    #         response = self.model_for_search.generate_content(user_request)
    #         return response.text.strip()
    #     except Exception as e:
    #         logger.error(f"Error fetching user request from Gemini: {e}")
    #         return "Error: Could not retrieve user request."
    
    # def fetch_daily_news(self):
    #     try:
    #         response = self.model_for_search.generate_content(prompts["searchRequestForNews"])
    #         return response.text.strip()
    #     except Exception as e:
    #         logger.error(f"Error fetching user request from Gemini: {e}")
    #         return "Error: Could not retrieve user request."
    
    # def fetch_daily_weather(self):
    #     try:
    #         response = self.model_for_search.generate_content(prompts["searchForWeather"], tools={"google_search_retrieval": {}})
    #         return response.text.strip()
    #     except Exception as e:
    #         logger.error(f"Error fetching user request from Gemini: {e}")
    #         return "Error: Could not retrieve user request."
    
    # def fetch_weekly_news(self):
    #     try:
    #         response = self.model_for_search.generate_content(prompts["searchWeeklyNews"])
    #         return response.text.strip()
    #     except Exception as e:
    #         logger.error(f"Error fetching user request from Gemini: {e}")
    #         return "Error: Could not retrieve user request."

    def fetch_daily_10_words(self):
        try:
            response = self.chat.send_message(
                prompts["learningWords"]
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching 10 words from Gemini: {e}")
            return "Error: Could not retrieve 10 words."
    
    def fetch_daily_words_reminder(self):
        try:
            response = self.chat.send_message(
                prompts["wordsReminders"]
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching reminders from Gemini: {e}")
            return "Error: Could not retrieve reminders."
