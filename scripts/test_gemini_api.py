#!/usr/bin/env python3
"""Test Gemini API directly to diagnose the issue."""

import os
from dotenv import load_dotenv

load_dotenv()

# Test 1: Direct Gemini API call
print("=" * 60)
print("Test 1: Direct Gemini API import and initialization")
print("=" * 60)

try:
    import google.generativeai as genai
    
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"API Key loaded: {api_key[:20]}..." if api_key else "❌ No API key")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    print("✅ Direct Gemini client initialized")
    
    # Simple test
    response = model.generate_content("Say 'Hello' in one word")
    print(f"✅ API call successful: {response.text}")
    
except Exception as e:
    print(f"❌ Direct API failed: {e}")

print()

# Test 2: LangChain ChatGoogleGenerativeAI
print("=" * 60)
print("Test 2: LangChain ChatGoogleGenerativeAI")
print("=" * 60)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.8,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    
    print("✅ LangChain Gemini initialized")
    
    # Simple test
    result = llm.invoke("Say 'Hello' in one word")
    print(f"✅ LangChain call successful: {result.content}")
    
except Exception as e:
    print(f"❌ LangChain failed: {type(e).__name__}: {e}")

print()
print("=" * 60)
print("Diagnosis complete")
print("=" * 60)
