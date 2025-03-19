#!/usr/bin/env python
"""
Example script demonstrating how to use the AI provider integrations.
"""

import asyncio
import os
import sys
import argparse
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from providers import factory

async def generate_chat_completion(
    provider: str,
    model: str,
    messages: List[Dict[str, str]],
    api_key: str,
    stream: bool = False,
    max_tokens: Optional[int] = None,
    temperature: float = 0.7
) -> Any:
    """Generate a chat completion using the specified provider and model."""
    try:
        response = await factory.generate_completion(
            provider_name=provider,
            model=model,
            messages=messages,
            api_key=api_key,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream
        )
        
        if stream:
            # Handle streaming response
            accumulated_text = ""
            async for chunk in response:
                if chunk.get("error", False):
                    print(f"\nError: {chunk['message']}")
                    return
                
                content = chunk.get("content", "")
                accumulated_text += content
                print(content, end="", flush=True)
            
            print("\n\n" + "-" * 50)
            print(f"Total tokens generated: {len(accumulated_text.split())} (approximate)")
            
        else:
            # Handle non-streaming response
            if response.get("error", False):
                print(f"Error: {response['message']}")
                return
            
            print(response["content"])
            print("\n" + "-" * 50)
            
            # Print token usage if available
            if "usage" in response and response["usage"]:
                usage = response["usage"]
                print(f"Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"Total tokens: {usage.get('total_tokens', 'N/A')}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate a chat completion using an AI provider")
    
    parser.add_argument("--provider", type=str, default="openai",
                        choices=["openai", "anthropic", "google", "cohere"],
                        help="The AI provider to use")
    
    parser.add_argument("--model", type=str,
                        help="The model ID to use (e.g., gpt-4, claude-3-opus-20240229)")
    
    parser.add_argument("--message", type=str, required=True,
                        help="The user message to send")
    
    parser.add_argument("--system", type=str, default="You are a helpful assistant.",
                        help="The system message for context")
    
    parser.add_argument("--stream", action="store_true",
                        help="Whether to stream the response")
    
    parser.add_argument("--max-tokens", type=int,
                        help="Maximum number of tokens to generate")
    
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Sampling temperature (0.0 to 1.0)")
    
    return parser.parse_args()

async def main():
    """Main function."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Default model selection based on provider if not specified
    if not args.model:
        default_models = {
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-haiku-20240307",
            "google": "gemini-pro",
            "cohere": "command"
        }
        args.model = default_models.get(args.provider)
    
    # Get API key from environment
    env_key_names = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "cohere": "COHERE_API_KEY"
    }
    
    api_key = os.environ.get(env_key_names.get(args.provider))
    
    if not api_key:
        print(f"Error: {env_key_names.get(args.provider)} not found in environment variables")
        return
    
    # Create messages array
    messages = [
        {"role": "system", "content": args.system},
        {"role": "user", "content": args.message}
    ]
    
    # Print request info
    print(f"Provider: {args.provider}")
    print(f"Model: {args.model}")
    print(f"Stream: {args.stream}")
    print(f"Temperature: {args.temperature}")
    print("-" * 50)
    
    # Generate completion
    await generate_chat_completion(
        provider=args.provider,
        model=args.model,
        messages=messages,
        api_key=api_key,
        stream=args.stream,
        max_tokens=args.max_tokens,
        temperature=args.temperature
    )

if __name__ == "__main__":
    asyncio.run(main())