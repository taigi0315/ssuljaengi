
import os
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from gossiptoon.core.config import ConfigManager

async def test_safety():
    try:
        config = ConfigManager()
        api_key = config.api.google_api_key
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        print("Testing Gemini 2.5 Flash with Safety Settings...")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            safety_settings=safety_settings,
        )
        
        # Try a prompt that might trigger filters (simulating intense drama logic)
        prompt = "Write a shocking, intense, and violent scene about a murder mystery reveal. Use screaming and aggressive language."
        
        response = await llm.ainvoke(prompt)
        print(f"Success! Response: {response.content}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_safety())
