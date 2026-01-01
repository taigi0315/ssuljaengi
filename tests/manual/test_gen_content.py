
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def test_generate_content_image():
    client = genai.Client(api_key=api_key)
    
    # Try generic Gemini 2.0 Flash Exp
    model = "gemini-2.0-flash-exp"
    print(f"\nTesting {model} with generate_content...")
    try:
        response = client.models.generate_content(
            model=model,
            contents="Generate an image of a cute cat.",
            config={'response_modalities': ['IMAGE']} # Maybe?
        )
        print("Response received.")
        # print(response)
        
        # Check for images
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    print("Found inline image data!")
                    with open("test_gen_content.png", "wb") as f:
                        f.write(part.inline_data.data)
                    return
                elif part.text:
                    print(f"Text response: {part.text}")
        
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_generate_content_image()
