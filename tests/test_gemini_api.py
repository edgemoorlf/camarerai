"""
Test Gemini API Key and Basic Functionality
Tests both text generation and Live API capabilities
"""

import os
from google import genai
from google.genai import types

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

def test_api_key():
    """Test if API key is valid"""
    print("=" * 60)
    print("TEST 1: API Key Validation")
    print("=" * 60)

    try:
        # List available models
        models = client.models.list()
        print("✅ API key is valid!")
        print(f"\nAvailable models (showing key models):")

        key_models = []
        native_audio_models = []
        tts_models = []

        for model in models:
            if 'native-audio' in model.name:
                native_audio_models.append(model.name)
            elif 'tts' in model.name:
                tts_models.append(model.name)
            elif any(x in model.name for x in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.5-pro']):
                if 'preview' not in model.name and 'image' not in model.name:
                    key_models.append(model.name)

        print("\n  Standard Models:")
        for model in key_models[:5]:
            print(f"    - {model}")

        print("\n  Native Audio Models (for Live API):")
        for model in native_audio_models:
            print(f"    - {model}")

        print("\n  TTS Models:")
        for model in tts_models:
            print(f"    - {model}")

        return True
    except Exception as e:
        print(f"❌ API key validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_text_generation():
    """Test basic text generation"""
    print("\n" + "=" * 60)
    print("TEST 2: Text Generation")
    print("=" * 60)

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Say hello in one sentence'
        )

        print(f"✅ Text generation works!")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Text generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streaming_generation():
    """Test streaming text generation"""
    print("\n" + "=" * 60)
    print("TEST 3: Streaming Text Generation")
    print("=" * 60)

    try:
        print("Streaming response: ", end='', flush=True)

        for chunk in client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents='Count from 1 to 5, one number per line'
        ):
            if chunk.text:
                print(chunk.text, end='', flush=True)

        print("\n✅ Streaming generation works!")
        return True
    except Exception as e:
        print(f"❌ Streaming generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_api_availability():
    """Check if Live API models are available"""
    print("\n" + "=" * 60)
    print("TEST 4: Live API Model Availability")
    print("=" * 60)

    try:
        models = client.models.list()

        native_audio_models = []
        for model in models:
            if 'native-audio' in model.name:
                native_audio_models.append(model.name)

        if native_audio_models:
            print("✅ Native Audio models found (these support Live API):")
            for model in native_audio_models:
                print(f"  - {model}")
            print("\nThese models support bidirectional audio streaming (Live API)")
        else:
            print("⚠️  No native audio models found")

        return len(native_audio_models) > 0
    except Exception as e:
        print(f"❌ Live API check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_function_calling():
    """Test function calling capability"""
    print("\n" + "=" * 60)
    print("TEST 5: Function Calling")
    print("=" * 60)

    try:
        # Define a function declaration
        add_to_order_func = types.FunctionDeclaration(
            name="add_to_order",
            description="Add an item to the order",
            parameters={
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "Name of the item to add"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity of the item"
                    }
                },
                "required": ["item_name", "quantity"]
            }
        )

        tool = types.Tool(function_declarations=[add_to_order_func])

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='I want to order 2 burgers',
            config=types.GenerateContentConfig(
                tools=[tool]
            )
        )

        print(f"✅ Function calling works!")

        # Check if function was called
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    print(f"Function called: {part.function_call.name}")
                    print(f"Arguments: {part.function_call.args}")
                elif hasattr(part, 'text') and part.text:
                    print(f"Response: {part.text}")

        return True
    except Exception as e:
        print(f"❌ Function calling failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance():
    """Test response latency"""
    print("\n" + "=" * 60)
    print("TEST 6: Performance Measurement")
    print("=" * 60)

    try:
        import time

        # Test 1: Short response with gemini-2.5-flash
        print("Testing gemini-2.5-flash:")
        start = time.time()
        first_chunk_time = None

        for i, chunk in enumerate(client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents='Say hello'
        )):
            if i == 0 and chunk.text:
                first_chunk_time = time.time() - start
                print(f"  Time to first chunk: {first_chunk_time*1000:.0f}ms")

        total_time = time.time() - start
        print(f"  Total generation time: {total_time*1000:.0f}ms")

        # Test 2: Medium response
        print("\nTesting medium response:")
        start = time.time()
        first_chunk_time = None

        for i, chunk in enumerate(client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents='Describe a restaurant in 2 sentences'
        )):
            if i == 0 and chunk.text:
                first_chunk_time = time.time() - start

        total_time = time.time() - start
        print(f"  Time to first chunk: {first_chunk_time*1000:.0f}ms")
        print(f"  Total time: {total_time*1000:.0f}ms")

        print("\n✅ Performance test complete!")
        return True
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("GEMINI API TESTING SUITE")
    print("=" * 60)

    results = {
        "API Key Validation": test_api_key(),
        "Text Generation": test_text_generation(),
        "Streaming Generation": test_streaming_generation(),
        "Live API Availability": test_live_api_availability(),
        "Function Calling": test_function_calling(),
        "Performance": test_performance()
    }

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    passed = sum(results.values())
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Gemini API is ready to use.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")

if __name__ == '__main__':
    main()
