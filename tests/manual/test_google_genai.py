
import asyncio
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def test_genai_sdk():
    print(f"Testing google-genai SDK (Key: {api_key[:5]}...)")
    
    try:
        client = genai.Client(api_key=api_key)
        print("Client initialized.")
        
        # Check available methods on client.models
        print(f"client.models attributes: {dir(client.models)}")
        
        # Try to generate image
        prompt = "A futuristic city skyline at sunset"
        
        try:
            print("Attempting generate_images with imagen-3.0-generate-001...")
            response = client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=prompt,
                config={'number_of_images': 1, 'aspect_ratio': '9:16'}
            )
            print("Success! (generate_images)")
            if response.generated_images:
                 response.generated_images[0].image.save("test_genai_image.png")
                 print("Saved to test_genai_image.png")
            return
        except Exception as e:
            print(f"generate_images failed: {e}")

        try:
            print("Attempting generate_content with gemini-2.0-flash-exp (just to check text)...")
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents='Hello'
            )
            print("Success! (generate_content text)")
        except Exception as e:
            print(f"generate_content failed: {e}")

    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    test_genai_sdk()
