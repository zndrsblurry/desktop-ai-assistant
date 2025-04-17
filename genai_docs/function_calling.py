"""
Function Calling with Gemini Live API

This snippet demonstrates how to use function calling (tools) with the Gemini Live API.
Function calling allows the model to take actions or retrieve information through
defined functions/tools during a conversation.

Key features:
- Defining tools in session configuration
- Sending natural language requests that trigger function calls
- Receiving and processing function call responses
- Text-only configuration for optimal function calling performance

Usage:
1. Define your functions/tools (like set_light_values in this example)
2. Include them in the LiveConnectConfig
3. Send user prompts that might trigger function calls
4. Process the function calls in your response handler

Note: Audio inputs and outputs negatively impact function calling performance.
This example uses text-only configuration for optimal function calling.
"""

config = types.LiveConnectConfig(
    response_modalities=["TEXT"],
    tools=[set_light_values]
)

async with client.aio.live.connect(model=model, config=config) as session:
    await session.send_client_content(
        turns={
            "role": "user",
            "parts": [{"text": "Turn the lights down to a romantic level"}],
        },
        turn_complete=True,
    )

    async for response in session.receive():
        print(response.tool_call)