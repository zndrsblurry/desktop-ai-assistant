import asyncio
from google import genai

"""
Send and Receive Text Example for Gemini Live API

This script demonstrates how to establish a bidirectional text conversation with
Gemini using the Live API. It creates a simple command-line interface where the user
can type messages and receive the model's responses in real-time.

Key features:
- Text-only conversation with Gemini
- Simple command-line interface
- Exit command handling ("exit" to end the conversation)
- Streaming responses from the model

Usage:
1. Replace "GEMINI_API_KEY" with your actual API key
2. Run the script
3. Type messages at the "User>" prompt
4. Type "exit" to end the conversation
"""

client = genai.Client(api_key="GEMINI_API_KEY")
model = "gemini-2.0-flash-live-001"  # Gemini 2.0 Flash model optimized for live interactions

config = {"response_modalities": ["TEXT"]}  # Configure for text-only responses

async def main():
    """Main function that handles the conversation loop with Gemini"""
    async with client.aio.live.connect(model=model, config=config) as session:
        while True:
            message = input("User> ")
            if message.lower() == "exit":
                break
            await session.send_client_content(
                turns={"role": "user", "parts": [{"text": message}]}, turn_complete=True
            )

            async for response in session.receive():
                if response.text is not None:
                    print(response.text, end="")

if __name__ == "__main__":
    asyncio.run(main())