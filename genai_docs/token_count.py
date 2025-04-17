from google.genai import types

"""
Token Count Tracking in Gemini Live API

This snippet demonstrates how to retrieve and monitor token usage during a Live API
session. Token counts are important for:
1. Monitoring API usage and costs
2. Ensuring you stay within context window limits
3. Optimizing prompts and responses

Key features:
- Accessing token usage metadata from server messages
- Breaking down tokens by modality
- Tracking total token count
- Pattern matching on response types

Usage:
1. Include this code in your response handling loop
2. Process the usage metadata when available
3. Use token counts for logging, billing, or optimization

Note: The server periodically sends usage metadata, not with every message.
This example shows how to extract this information when it's available.
"""

async with client.aio.live.connect(
    model='gemini-2.0-flash-live-001',
    config=types.LiveConnectConfig(
        response_modalities=['AUDIO'],
    ),
) as session:
    # Session connected
    while True:
        await session.send_client_content(
            turns=types.Content(role='user', parts=[types.Part(text='Hello world!')])
        )
        async for message in session.receive():
            # The server will periodically send messages that include
            # UsageMetadata.
            if message.usage_metadata:
                usage = message.usage_metadata
                print(
                    f'Used {usage.total_token_count} tokens in total. Response token'
                    ' breakdown:'
                )
            for detail in usage.response_tokens_details:
                match detail:
                  case types.ModalityTokenCount(modality=modality, token_count=count):
                      print(f'{modality}: {count}')

            # For the purposes of this example, placeholder input is continually fed
            # to the model. In non-sample code, the model inputs would come from
            # the user.
            if message.server_content and message.server_content.turn_complete:
                break