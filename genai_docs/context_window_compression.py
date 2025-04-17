from google.genai import types

"""
Context Window Compression for Gemini Live API

This snippet demonstrates how to enable context window compression for longer
sessions with the Gemini Live API. This feature helps avoid abrupt connection
terminations due to context window limits.

Key features:
- Enabling sliding window compression mechanism
- Configuring compression parameters
- Extending session duration limits
- Maintaining conversation continuity

Session duration limits:
- Without compression: 15 minutes for audio-only, 2 minutes for audio+video
- With compression: Unlimited session duration

How it works:
- The sliding window mechanism compresses or summarizes older parts of the conversation
- This frees up context window space for new interactions
- The compression trigger can be configured based on token counts

Usage:
1. Include context_window_compression in your LiveConnectConfig
2. Configure the sliding window mechanism as needed
3. Enjoy extended session duration limits

Note: This is essential for applications requiring longer conversations.
"""

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    context_window_compression=(
        # Configures compression with default parameters.
        types.ContextWindowCompressionConfig(
            sliding_window=types.SlidingWindow(),
        )
    ),
)