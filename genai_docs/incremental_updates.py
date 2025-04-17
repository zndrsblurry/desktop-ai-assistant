"""
Incremental Content Updates for Gemini Live API

This snippet demonstrates how to send incremental content updates to establish or
restore session context with the Gemini Live API. This approach is useful for:
1. Sending text input in chunks
2. Establishing initial context for a conversation
3. Restoring context from previous interactions

Key features:
- Turn-by-turn interaction representation
- Handling both user and model messages
- Control over turn completion status
- Support for conversation history

Usage:
- For short contexts: Send turn-by-turn interactions
- For longer contexts: Provide a single message summary to free up context window

Note: This example shows how to send previous conversation history (France question)
followed by a new question (Germany question) in two separate updates.
"""

turns = [
    {"role": "user", "parts": [{"text": "What is the capital of France?"}]},
    {"role": "model", "parts": [{"text": "Paris"}]},
]

await session.send_client_content(turns=turns, turn_complete=False)

turns = [{"role": "user", "parts": [{"text": "What is the capital of Germany?"}]}]

await session.send_client_content(turns=turns, turn_complete=True)