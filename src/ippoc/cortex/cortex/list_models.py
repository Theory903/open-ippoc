import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("brain/cortex/.env")

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("No API Key found")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
