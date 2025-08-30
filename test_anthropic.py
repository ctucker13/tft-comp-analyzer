# test_anthropic.py
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"API key: {api_key[:20]}..." if api_key else "No API key found")

if api_key and api_key != "your_anthropic_key_here":
    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Updated model
            max_tokens=100,
            messages=[{"role": "user", "content": "Say 'API working' if you can read this."}]
        )
        print(f"✅ Anthropic API working: {response.content[0].text}")
    except Exception as e:
        print(f"❌ Anthropic API error: {e}")
else:
    print("❌ No valid Anthropic API key")