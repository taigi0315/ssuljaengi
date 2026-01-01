
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def test_specific_models():
    client = genai.Client(api_key=api_key)
    
    models_to_test = [
        "imagen-4.0-fast-generate-001",
        "gemini-2.5-flash-image",
        "gemini-2.0-flash-exp-image-generation"
    ]
    
    for model in models_to_test:
        print(f"\nTesting model: {model}")
        try:
            response = client.models.generate_images(
                model=model,
                prompt="A cute cat",
                config={'number_of_images': 1, 'aspect_ratio': '1:1'}
            )
            print(f"Success! Generated {len(response.generated_images)} images.")
            response.generated_images[0].image.save(f"test_{model}.png")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_specific_models()
