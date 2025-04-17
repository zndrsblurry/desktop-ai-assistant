from google.genai import types

"""
Session Resumption with Gemini Live API

This snippet demonstrates how to implement session resumption in the Gemini Live API.
Session resumption allows conversations to continue after temporary disconnections
or server resets, preserving context and conversation history.

Key features:
- Configuring session resumption in connection setup
- Processing SessionResumptionUpdate messages
- Storing and using session handles
- Seamless conversation continuity

How it works:
1. The server periodically sends SessionResumptionUpdate messages with handles
2. These handles are stored by the client
3. On reconnection, the client provides the latest handle
4. The session resumes with preserved context

Usage:
1. Include session_resumption in your LiveConnectConfig
2. Process and store session handles from update messages
3. Use the latest handle when reconnecting

Note: Session data is stored on the server for 24 hours.
"""

print(f"Connecting to the service with handle {previous_session_handle}...")
async with client.aio.live.connect(
    model="gemini-2.0-flash-live-001",
    config=types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        session_resumption=types.SessionResumptionConfig(
            # The handle of the session to resume is passed here,
            # or else None to start a new session.
            handle=previous_session_handle
        ),
    ),
) as session:
    # Session connected
    while True:
        await session.send_client_content(
            turns=types.Content(
                role="user", parts=[types.Part(text="Hello world!")]
            )
        )
        async for message in session.receive():
            # Periodically, the server will send update messages that may
            # contain a handle for the current state of the session.
            if message.session_resumption_update:
                update = message.session_resumption_update
                if update.resumable and update.new_handle:
                    # The handle should be retained and linked to the session.
                    return update.new_handle

            # For the purposes of this example, placeholder input is continually fed
            # to the model. In non-sample code, the model inputs would come from
            # the user.
            if message.server_content and message.server_content.turn_complete:
                break