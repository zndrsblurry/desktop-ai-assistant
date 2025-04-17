from google.genai import types

"""
Voice Configuration for Gemini Live API

This snippet demonstrates how to configure a specific voice for Gemini's audio responses.
The Live API supports multiple voice options that can be specified during session setup.

Available voices:
- Puck
- Charon
- Kore
- Fenrir
- Aoede
- Leda
- Orus
- Zephyr

Key features:
- Setting specific voice for model responses
- Using strongly typed configuration objects
- Configuring audio output

Usage:
1. Choose one of the available voice options
2. Use this config when establishing a Live API connection
3. All audio responses will use the specified voice

Note: This example configures the "Kore" voice, but can be modified to use any
of the available voices listed above.
"""

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    )
)