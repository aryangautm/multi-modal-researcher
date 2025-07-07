from google.genai import Client

from .config import settings

genai_client = Client(api_key=settings.GEMINI_API_KEY)
