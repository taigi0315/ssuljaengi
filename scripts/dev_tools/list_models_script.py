
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def list_models():
    client = genai.Client(api_key=api_key)
    print("Listing models...")
    try:
        models = client.models.list()
        for m in models:
            print(f"Model: {m.name}")
            # print(f"  Info: {m}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
