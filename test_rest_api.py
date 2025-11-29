import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("Available Models:")
            for m in models:
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    print(f"- {m['name']}")
            return True
        else:
            print(f"Error listing models: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    list_models()
