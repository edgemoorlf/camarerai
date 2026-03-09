"""
Automated test for Gemini Live API
Tests connection, audio streaming, and function calling without browser
"""

import asyncio
import os
import sys
import base64
from dotenv import load_dotenv

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from services.gemini_live_service import GeminiLiveService
from services.order_service import OrderService
import config


class MockEmitter:
    """Mock SocketIO emitter that prints events"""
    def __init__(self):
        self.events = []

    def __call__(self, event, data):
        self.events.append((event, data))
        print(f"  [Event] {event}: {list(data.keys())}")


async def test_gemini_connection():
    """Test basic Gemini Live API connection"""
    print("\n" + "="*60)
    print("TEST 1: Gemini Live API Connection")
    print("="*60)

    try:
        service = GeminiLiveService()
        emitter = MockEmitter()

        await service.connect(
            session_id="test-session-001",
            emit_func=emitter,
            order_service=OrderService(),
            tools=[config.ORDER_UPDATE_TOOL]
        )

        print("✓ Connected successfully")
        print(f"  Session ID: {service.session_id}")
        print(f"  Model: {service.model}")

        await service.disconnect()
        print("✓ Disconnected cleanly")
        return True

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_audio_receive():
    """Test receiving audio from Gemini"""
    print("\n" + "="*60)
    print("TEST 2: Audio Reception")
    print("="*60)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        emitter = MockEmitter()

        config_obj = types.LiveConnectConfig(
            response_modalities=['AUDIO'],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Aoede')
                )
            )
        )

        print("Connecting...")
        async with client.aio.live.connect(model=config.GEMINI_LIVE_MODEL, config=config_obj) as session:
            print("✓ Connected")

            # Send a simple message
            print("Sending message...")
            await session.send_client_content(
                turns=[types.Content(role='user', parts=[types.Part(text='Say hello')])],
                turn_complete=True
            )

            # Receive audio
            print("Receiving audio...")
            audio_chunks = 0
            total_bytes = 0

            async for message in session.receive():
                if message.server_content and message.server_content.model_turn:
                    for part in message.server_content.model_turn.parts:
                        if part.inline_data:
                            audio_chunks += 1
                            total_bytes += len(part.inline_data.data)
                            print(f"  Audio chunk {audio_chunks}: {len(part.inline_data.data)} bytes")

                        if part.text:
                            print(f"  Text: {part.text[:50]}...")

                if message.server_content and message.server_content.turn_complete:
                    print(f"✓ Turn complete ({audio_chunks} chunks, {total_bytes} bytes)")
                    break

        print("✓ Session closed")
        return audio_chunks > 0

    except Exception as e:
        print(f"✗ Audio test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_function_calling():
    """Test function calling with order updates"""
    print("\n" + "="*60)
    print("TEST 3: Function Calling")
    print("="*60)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GEMINI_API_KEY)

        # Define order update tool
        order_tool = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="update_order",
                    description="Update the customer's food order",
                    parameters={
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["add", "modify", "remove"]},
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "quantity": {"type": "integer"},
                                        "price": {"type": "number"}
                                    },
                                    "required": ["name", "quantity", "price"]
                                }
                            }
                        },
                        "required": ["action", "items"]
                    }
                )
            ]
        )

        config_obj = types.LiveConnectConfig(
            response_modalities=['AUDIO'],
            tools=[order_tool]
        )

        print("Connecting with tool...")
        async with client.aio.live.connect(model=config.GEMINI_LIVE_MODEL, config=config_obj) as session:
            print("✓ Connected")

            # Send a message that should trigger function call
            print("Sending order request...")
            await session.send_client_content(
                turns=[types.Content(role='user', parts=[types.Part(text='I want to order 2 burgers for $10 each')])],
                turn_complete=True
            )

            # Receive and check for function calls
            function_called = False
            async for message in session.receive():
                if message.tool_call:
                    function_called = True
                    print(f"✓ Function call received!")
                    for call in message.tool_call.function_calls:
                        print(f"  Function: {call.name}")
                        print(f"  Args: {call.args}")

                    # Send response back
                    await session.send_tool_response(
                        function_responses=[
                            types.FunctionResponse(
                                id=message.tool_call.function_calls[0].id,
                                response={"status": "success", "order_id": "123"}
                            )
                        ]
                    )
                    print("✓ Tool response sent")

                if message.server_content and message.server_content.turn_complete:
                    break

        if not function_called:
            print("⚠ No function call triggered (may need different prompt)")
        return function_called

    except Exception as e:
        print(f"✗ Function calling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("="*60)
    print("GEMINI LIVE API AUTOMATED TESTS")
    print("="*60)
    print(f"Model: {config.GEMINI_LIVE_MODEL}")
    print(f"API Key: {config.GEMINI_API_KEY[:15]}...{config.GEMINI_API_KEY[-4:]}")

    results = []

    # Run tests
    results.append(("Connection", await test_gemini_connection()))
    results.append(("Audio Reception", await test_audio_receive()))
    results.append(("Function Calling", await test_function_calling()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")

    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{len(results)} tests passed")

    return all(p for _, p in results)


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
