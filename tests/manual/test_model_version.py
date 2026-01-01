
import os
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from gossiptoon.core.config import ConfigManager

async def test_gemini_2_5():
    try:
        config = ConfigManager()
        api_key = config.api.google_api_key
        
        print(f"Testing Gemini 2.5 Flash with API Key: {api_key[:5]}...")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key
        )
        
        response = await llm.ainvoke("Hello, are you online?")
        print(f"Success! Response: {response.content}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_gemini_2_5())
