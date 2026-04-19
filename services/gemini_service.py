
from utils.logger import get_logger
from prompts.prompts import prompts
from google import genai
from google.genai import types
import json
import os
import io

logger = get_logger(__name__)

class GeminiService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash" 
        self.model_for_search = "gemini-2.5-flash"
        self.tutor_model = "gemini-2.5-flash" 
        self.output_audio_model = "gemini-2.5-flash-preview-tts"
        self.sessions_file = "data/sessions.json"
        
        os.makedirs("data", exist_ok=True)
        self.user_sessions = self._load_sessions()
        
        self.tutor_instruction = types.GenerateContentConfig(
            system_instruction=prompts.get("historySetUP", "You are a helpful Polish language tutor.")
        )

    def _load_sessions(self):
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
        return {}

    def _save_sessions(self):
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def _get_history(self, user_id: str):
        if str(user_id) not in self.user_sessions:
            self.user_sessions[str(user_id)] = []
        return self.user_sessions[str(user_id)]

    def _update_history(self, user_id: str, role: str, text: str):
        history = self._get_history(user_id)
        if len(history) > 20:
            history.pop(0)
        history.append({"role": role, "parts": [{"text": text}]})
        self._save_sessions()

    def upload_file(self, path):
        try:
            return self.client.files.upload(file=path)
        except Exception as e:
            logger.error(f"Error uploading file to Gemini: {e}")
            return None

    def describe_image(self, uploaded_file, user_prompt: str) -> str:
        try:
            result = self._generate_content_with_retry(
                model=self.model,
                contents=[uploaded_file, "\n\n", user_prompt]
            )
            return result.text
        except Exception as e:
            logger.error(f"Error describing image: {e}")
            return "Przepraszam, wystąpił błąd podczas analizy obrazu przez AI."

    def _generate_content_with_retry(self, *args, **kwargs):
        import time
        max_retries = 3
        delay = 60
        last_e = None
        for attempt in range(1, max_retries + 1):
            try:
                return self.client.models.generate_content(*args, **kwargs)
            except Exception as e:
                last_e = e
                logger.warning(f"Google API Error: {e}. Retry {attempt}/{max_retries} in {delay}s...")
                if attempt < max_retries:
                    time.sleep(delay)
        
        logger.error("All 3 retries failed to get a successful response from Gemini.")
        raise last_e

    def _send_text_with_history(self, user_id: str, prompt: str) -> str:
        try:
            history = self._get_history(user_id)
            contents = [types.Content(role=h["role"], parts=[types.Part(text=h["parts"][0]["text"])]) for h in history]
            contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
            
            response = self._generate_content_with_retry(
                model=self.tutor_model,
                contents=contents,
                config=self.tutor_instruction
            )
            
            self._update_history(user_id, "user", prompt)
            self._update_history(user_id, "model", response.text.strip())
            
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            return "Error: Could not retrieve response."
    
    def fetch_user_request(self, user_request: str, user_id: str = "global"):
        return self._send_text_with_history(user_id, user_request)

    def fetch_user_search_request(self, user_request: str):
        try:
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(tools=[grounding_tool])
            response = self._generate_content_with_retry(
                model=self.model_for_search,
                contents=user_request,
                config=config
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error fetching search request: {e}")
            return "Error: Could not retrieve search request."
    
    def _pcm_to_wav_bytes(self, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> bytes:
        import wave
        import io
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)
        return buffer.getvalue()

    def handle_audio_search_request(self, audio_bytes: bytes, mime_type: str = "audio/ogg", play_audio: bool = False, perform_search: bool = False):
        """
        Takes raw audio bytes, passes them to Gemini for speech-to-text / analysis,
        and asks for an audio response back. Optionally uses Search Grounding.
        """
        try:
            audio_part = types.Part(
                inline_data=types.Blob(
                    data=audio_bytes,
                    mime_type=mime_type
                )
            )
            transcription_response = self._generate_content_with_retry(
                model=self.model,
                contents=[audio_part, "Please transcribe this audio exactly to text. Do not answer questions, just provide the transcription."],
            )
            user_question_text = transcription_response.text.strip()
            logger.info(f"Audio transcription complete: {user_question_text}")

            tools = [types.Tool(google_search=types.GoogleSearch())]
            search_config = types.GenerateContentConfig(
                tools=tools,
                response_modalities=["TEXT"],
                system_instruction="Answer the user's query accurately, but in super short form, 10 sentance max. Respond in language the user is asking in."
            )
            
            answer_response = self._generate_content_with_retry(
                model=self.model_for_search, # gemini-2.5-flash
                contents=user_question_text,
                config=search_config
            )
            text_response = answer_response.text.strip()
            logger.info(f"Search and answer complete. Text response: {text_response[:100]}...")

            if not play_audio:
                return text_response, None

            tts_config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Kore" # Using a natural voice
                        )
                    )
                )
            )
            
            audio_gen_response = self._generate_content_with_retry(
                model=self.output_audio_model, 
                contents=text_response, 
                config=tts_config
            )

            audio_bytes_response = None
            if audio_gen_response.candidates:
                for candidate in audio_gen_response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if part.inline_data and part.inline_data.data:
                                audio_bytes_response = part.inline_data.data
                                break
                            elif hasattr(part, 'blob') and part.blob.data:
                                audio_bytes_response = part.blob.data
                                break
                    if audio_bytes_response: break

            if audio_bytes_response:
                logger.info(f"Successfully generated speech. PCM Bytes size: {len(audio_bytes_response)}")
                audio_bytes_response = self._pcm_to_wav_bytes(audio_bytes_response)
            else:
                logger.warning(f"Generation model {self.output_audio_model} failed to produce audio bytes.")

            return text_response, audio_bytes_response

        except Exception as e:
            logger.error(f"Error in three-step audio pipeline: {e}")
            return "Przepraszam, usługa Google Gemini jest przeciążona (błąd 503). Spróbowałem 3 razy, ale nadal nie działa. Spróbuj powtórzyć pytanie za kilka minut.", None

    def fetch_daily_audio_dialog(self) -> bytes:
        """
        Triggers Gemini to generate a Polish dialog audio snippet for the scheduler.
        """

        try:
            transcript_prompt = prompts.get("audioDialog", "Generate a natural 3-4 min Polish podcast between Marek and Anna about a fun scientific fact.")
            transcript_prompt += "\nFormat the response strictly as a transcript with speaker names: 'Marek: ...' and 'Anna: ...'."
            
            transcript = self._send_text_with_history("daily_learning", transcript_prompt)
            logger.info("Transcript for multi-speaker dialog generated.")

            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=[
                            types.SpeakerVoiceConfig(
                                speaker='Marek',
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Puck')
                                )
                            ),
                            types.SpeakerVoiceConfig(
                                speaker='Anna',
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Kore')
                                )
                            ),
                        ]
                    )
                )
            )
            
            response = self._generate_content_with_retry(
                model=self.output_audio_model,
                contents=transcript,
                config=config
            )
            
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if part.inline_data and part.inline_data.data:
                                logger.info(f"Multi-speaker dialog generated. Size: {len(part.inline_data.data)}")
                                return self._pcm_to_wav_bytes(part.inline_data.data)
                            elif hasattr(part, 'blob') and part.blob.data:
                                logger.info(f"Multi-speaker dialog generated (blob). Size: {len(part.blob.data)}")
                                return self._pcm_to_wav_bytes(part.blob.data)
            
            logger.warning(f"Multi-speaker dialog synthesis failed. Response: {response}")
            return None
        except Exception as e:
            logger.error(f"Error in multi-speaker dialog pipeline: {e}")
            return None

    def fetch_daily_text(self):
        try:
            return self._send_text_with_history("daily_learning", prompts["lerningText"])
        except Exception as e:
            return "Error: Could not retrieve daily text."

    def fetch_daily_quiz(self):
        try:
            return self._send_text_with_history("daily_learning", prompts["learningQuiz"])
        except Exception as e:
            return "Error: Could not retrieve daily quiz."

    def fetch_daily_news(self):
        try:
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(tools=[grounding_tool])
            response = self._generate_content_with_retry(
                model=self.model_for_search,
                contents=prompts["searchRequestForNews"],
                config=config
            )
            return response.text.strip()
        except Exception as e:
            return "Error: Could not retrieve daily news."

    def fetch_daily_weather(self):
        try:
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(tools=[grounding_tool])
            response = self._generate_content_with_retry(
                model=self.model_for_search,
                contents=prompts["searchForWeather"],
                config=config
            )
            return response.text.strip()
        except Exception as e:
            return "Error: Could not retrieve daily weather."

    def fetch_weekly_news(self):
        try:
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(tools=[grounding_tool])
            response = self._generate_content_with_retry(
                model=self.model_for_search,
                contents=prompts["searchWeeklyNews"],
                config=config
            )
            return response.text.strip()
        except Exception as e:
            return "Error: Could not retrieve weekly news."

    def fetch_daily_10_words(self):
        try:
            return self._send_text_with_history("daily_learning", prompts["learningWords"])
        except Exception as e:
            return "Error: Could not retrieve 10 words."

    def fetch_daily_words_reminder(self):
        try:
            return self._send_text_with_history("daily_learning", prompts["wordsReminders"])
        except Exception as e:
            return "Error: Could not retrieve reminders."

    def fetch_history_words_reminder(self):
        try:
            return self._send_text_with_history("daily_learning", prompts["historyWordsReminder"])
        except Exception as e:
            return "Error: Could not retrieve history words reminder."
