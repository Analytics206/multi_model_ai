#!/usr/bin/env python
"""
Simple test script to verify provider integration works.
"""

import asyncio
import os
from dotenv import load_dotenv
import sys

# Make sure we can import the providers module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from providers import factory

async def test_anthropic():
    """Test Anthropic provider."""
    print("\n===== Testing Anthropic Provider =====")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables")
        return False
    
    try:
        # Create messages
        messages = [
            {"role": "system", "content": "You are Claude, a helpful AI assistant."},
            {"role": "user", "content": "What is 2+2? Answer with just the number."}
        ]
        
        # Generate completion
        print("Sending request to Anthropic...")
        response = await factory.generate_completion(
            provider_name="anthropic",
            model="claude-3-haiku-20240307",  # Use a model that exists in your account
            messages=messages,
            api_key=api_key,
            temperature=0.7
        )
        
        print("\nResponse:")
        print(response["content"])
        
        if "usage" in response:
            print("\nToken Usage:")
            print(f"Prompt tokens: {response['usage'].get('prompt_tokens', 'N/A')}")
            print(f"Completion tokens: {response['usage'].get('completion_tokens', 'N/A')}")
            print(f"Total tokens: {response['usage'].get('total_tokens', 'N/A')}")
        
        print("\nTest successful! ✅")
        return True
    except Exception as e:
        print(f"\nError testing Anthropic provider: {str(e)}")
        print("Test failed! ❌")
        return False

async def test_streaming():
    """Test streaming with Anthropic provider."""
    print("\n===== Testing Streaming with Anthropic Provider =====")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables")
        return False
    
    try:
        # Create messages
        messages = [
            {"role": "system", "content": "You are Claude, a helpful AI assistant."},
            {"role": "user", "content": "Count from 1 to 5 with a short pause between each number."}
        ]
        
        # Generate streaming completion
        print("Sending streaming request to Anthropic...")
        stream = await factory.generate_completion(
            provider_name="anthropic",
            model="claude-3-haiku-20240307",
            messages=messages,
            api_key=api_key,
            temperature=0.7,
            stream=True
        )
        
        print("\nResponse (streaming):")
        async for chunk in stream:
            if chunk.get("error", False):
                print(f"\nError: {chunk['message']}")
                return False
            
            print(chunk["content"], end="", flush=True)
        
        print("\n\nStreaming test successful! ✅")
        return True
    except Exception as e:
        print(f"\nError testing Anthropic streaming: {str(e)}")
        print("Streaming test failed! ❌")
        return False

async def main():
    """Run all tests."""
    print("Starting provider integration tests...")
    # Load environment variables
    load_dotenv()
    
    # Run tests
    regular_test = await test_anthropic()
    
    if regular_test:
        streaming_test = await test_streaming()
    else:
        print("\nSkipping streaming test due to failed regular test.")
        streaming_test = False
    
    # Summary
    print("\n===== Test Summary =====")
    print(f"Regular API test: {'✅ Passed' if regular_test else '❌ Failed'}")
    print(f"Streaming API test: {'✅ Passed' if streaming_test else '❌ Failed'}")
    
    if regular_test and streaming_test:
        print("\nAll tests passed! The provider integration is working correctly.")
    else:
        print("\nSome tests failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())