from google.genai import types

"""
Media Resolution Configuration for Gemini Live API

This snippet demonstrates how to configure media resolution for input media
in the Gemini Live API. This setting controls the resolution used for processing
images and video input.

Key features:
- Setting specific media resolution for inputs
- Optimizing for different use cases and bandwidth requirements
- Balancing quality and performance

Available resolutions:
- MEDIA_RESOLUTION_LOW: Uses less bandwidth, faster processing (66/256 tokens)
- MEDIA_RESOLUTION_HIGH: Higher quality, more bandwidth (default)

Usage:
1. Include media_resolution in your LiveConnectConfig
2. Choose the appropriate resolution based on your requirements
3. Consider bandwidth and latency constraints

Note: Lower resolution reduces bandwidth usage and can improve performance
on slower connections or when processing speed is critical.
"""

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
)