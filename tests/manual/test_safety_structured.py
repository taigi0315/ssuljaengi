
import os
import asyncio
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from gossiptoon.core.config import ConfigManager

class ViolentScene(BaseModel):
    description: str = Field(..., description="Description of the scene")
    intensity: int = Field(..., description="Intensity level 1-10")

async def test_safety_structured():
    try:
        config = ConfigManager()
        api_key = config.api.google_api_key
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        print("Testing Gemini 2.5 Flash Structured Output with Safety Settings...")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            safety_settings=safety_settings,
        )
        
        structured_llm = llm.with_structured_output(ViolentScene)
        
        # Try a prompt that might trigger filters
        prompt = "Write a shocking, intense, and violent scene about a murder mystery reveal. Use screaming and aggressive language."
        
        response = await structured_llm.ainvoke(prompt)
        print(f"Success! Response: {response}")
        return True
    except Exception as e:
        # print full error details
        import traceback
        traceback.print_exc()
        print(f"Failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_safety_structured())
