"""
Handling User Interruptions in Gemini Live API

This snippet demonstrates how to detect and handle interruptions in the Gemini Live API.
Users can interrupt the model's output at any time, and the API provides mechanisms
to detect these interruptions.

Key features:
- Detecting user interruptions during model generation
- Graceful handling of interrupted responses
- Identifying canceled function calls
- Managing conversation flow after interruptions

Behavior on interruption:
- Ongoing generation is canceled and discarded
- Only information already sent to client is retained in session history
- Pending function calls are discarded
- The server sends interruption notification

Usage:
1. Include this code in your response handling loop
2. Implement appropriate UI feedback or conversation adjustments when interrupted

Note: This is particularly important for voice interfaces where users
may naturally interrupt the model.
"""

async for response in session.receive():
    if response.server_content.interrupted is not None:
        # The generation was interrupted