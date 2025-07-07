import os

from dotenv import load_dotenv
from google.genai import Client

load_dotenv()

genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))
