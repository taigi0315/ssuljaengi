
import os
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from gossiptoon.models.script import Script
from gossiptoon.core.config import ConfigManager

async def test_schema_warning():
    print("Testing schema conversion for warnings...")
    
    config = ConfigManager()
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=config.api.google_api_key,
    )
    
    # This line triggers the conversion and should show the warning
    # "Key 'example' is not supported in schema, ignoring"
    try:
        structured_llm = llm.with_structured_output(Script)
        print("Schema conversion completed.")
    except Exception as e:
        print(f"Error during conversion: {e}")

if __name__ == "__main__":
    asyncio.run(test_schema_warning())
