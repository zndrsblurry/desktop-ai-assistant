import asyncio
import wave
from google import genai

"""
Receive Audio Example for Gemini Live API

This script demonstrates how to receive audio output from Gemini using the Live API.
It sends a text prompt to Gemini and saves the audio response to a WAV file.

Key features:
- Text input to Gemini
- Audio output from Gemini
- Saving audio to a WAV file
- Using v1alpha API version

Audio format details:
- Output audio format: Raw 16-bit PCM audio at 24kHz little-endian
- Mono channel (1 channel)
- Sample width: 2 bytes

Usage:
1. Replace "GEMINI_API_KEY" with your actual API key
2. Run the script
3. Check the created "audio.wav" file
"""

client = genai.Client(api_key="GEMINI_API_KEY", http_options={'api_version': 'v1alpha'})
model = "gemini-2.0-flash-live-001"  # Gemini 2.0 Flash model optimized for live interactions

config = {"response_modalities": ["AUDIO"]}  # Configure for audio-only responses

async def main():
    """Main function that handles sending a text prompt and receiving audio response"""
    async with client.aio.live.connect(model=model, config=config) as session:
        wf = wave.open("audio.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)

        message = "Hello? Gemini are you there?"
        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": message}]}, turn_complete=True
        )

        async for idx, response in async_enumerate(session.receive()):
            if response.data is not None:
                wf.writeframes(response.data)

            # Un-comment this code to print audio data info
            # if response.server_content.model_turn is not None:
            #      print(response.server_content.model_turn.parts[0].inline_data.mime_type)

        wf.close()

if __name__ == "__main__":
    asyncio.run(main())