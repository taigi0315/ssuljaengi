
import os
import asyncio
from typing import List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from gossiptoon.core.config import ConfigManager

class Step(BaseModel):
    step_id: int
    description: str = Field(..., description="Action step")
    tools_needed: List[str] = Field(..., description="List of tools")

class Plan(BaseModel):
    title: str
    steps: List[Step]

async def test_structured_output():
    try:
        config = ConfigManager()
        api_key = config.api.google_api_key
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key
        )
        
        structured_llm = llm.with_structured_output(Plan)
        
        print("Testing structured output with Gemini 2.5 Flash...")
        response = await structured_llm.ainvoke("Make a plan to clean the kitchen.")
        
        print(f"Success! Response type: {type(response)}")
        print(response)
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_structured_output())
