# Gemini Live API Examples

This repository contains code examples for working with Google's Gemini Live API, which enables low-latency bidirectional voice and video interactions with Gemini models.

## Overview

The Live API allows for natural, human-like voice conversations with the ability to interrupt the model's responses using voice commands. It can process text, audio, and video input, and provide text and audio output.

## Examples

The following Python examples demonstrate key features of the Gemini Live API:

1. **[send_receive_text.py](send_receive_text.py)** - Basic example for establishing a bidirectional text conversation with Gemini.

2. **[receive_audio.py](receive_audio.py)** - Example for receiving audio output from Gemini and saving it to a WAV file.

3. **[system_instructions.py](system_instructions.py)** - Setting system instructions to steer the model's behavior throughout a session.

4. **[incremental_updates.py](incremental_updates.py)** - How to send incremental content updates to establish or restore session context.

5. **[change_voices.py](change_voices.py)** - Configuring different voice options for Gemini's audio responses.

6. **[function_calling.py](function_calling.py)** - Using function calling (tools) to enable the model to take actions or retrieve information.

7. **[handling_interruptions.py](handling_interruptions.py)** - Detecting and handling user interruptions during model generation.

8. **[token_count.py](token_count.py)** - Tracking token usage during a Live API session.

9. **[session_resumption.py](session_resumption.py)** - Implementing session resumption after disconnections, preserving context.

10. **[context_window_compression.py](context_window_compression.py)** - Enabling context window compression for longer sessions.

11. **[media_resolution.py](media_resolution.py)** - Configuring media resolution for input media processing.

12. **[full_livestream_example.py](full_livestream_example.py)** - Complete example with audio, video, and text communication, supporting both camera and screen capture modes.

## Key Features

- **Bidirectional Communication**: Real-time interaction with the model
- **Multimodal Support**: Text, audio, and video inputs and outputs
- **Interruption Handling**: Users can interrupt the model's responses
- **Session Management**: Session resumption and context window compression
- **Voice Configuration**: Multiple voice options for audio output
- **Function Calling**: Enable the model to take actions through defined functions
- **Customizable Behavior**: System instructions to steer model behavior

## Usage Notes

- Replace `"GEMINI_API_KEY"` in the examples with your actual Gemini API key
- The Live API requires server-to-server authentication and isn't recommended for direct client use
- Audio-only sessions are limited to 15 minutes without compression
- Audio plus video sessions are limited to 2 minutes without compression
- Session duration can be extended by enabling compression

## Audio Formats

- **Input audio format**: Raw 16-bit PCM audio at 16kHz little-endian
- **Output audio format**: Raw 16-bit PCM audio at 24kHz little-endian

## Session Duration

- With compression: Unlimited session duration
- Without compression:
  - Audio-only: 15 minutes
  - Audio+video: 2 minutes
