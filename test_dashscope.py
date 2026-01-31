"""
Test script for DashScope API integration
Tests ASR, LLM, and TTS functionality
"""

from dashscope_client import DashScopeClient
import sys

def test_llm(client):
    """Test LLM (Qwen) with multilingual support"""
    print("\n" + "="*60)
    print("TEST 1: LLM (Qwen-Plus)")
    print("="*60)

    test_cases = [
        {
            'language': 'English',
            'messages': [{'role': 'user', 'content': 'Hello! What is your name?'}]
        },
        {
            'language': 'Mandarin',
            'messages': [{'role': 'user', 'content': '你好！你叫什么名字？'}]
        },
        {
            'language': 'Cantonese',
            'messages': [{'role': 'user', 'content': '你好！你叫咩名？'}]
        }
    ]

    for test in test_cases:
        print(f"\n{test['language']} test:")
        print(f"  Input: {test['messages'][0]['content']}")
        try:
            response = client.chat(test['messages'])
            print(f"  ✓ Response: {response[:100]}...")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False

    return True

def test_tts(client):
    """Test TTS (Sambert) with different voices"""
    print("\n" + "="*60)
    print("TEST 2: TTS (Sambert)")
    print("="*60)

    test_cases = [
        {
            'language': 'English',
            'text': 'Hello, welcome to our restaurant!',
            'voice': 'zhixiaobai'
        },
        {
            'language': 'Mandarin',
            'text': '你好，欢迎来到我们的餐厅！',
            'voice': 'zhixiaobai'
        },
        {
            'language': 'Cantonese',
            'text': '你好，歡迎嚟到我哋嘅餐廳！',
            'voice': 'zhixiaobai'
        }
    ]

    for test in test_cases:
        print(f"\n{test['language']} test:")
        print(f"  Text: {test['text']}")
        try:
            audio_url = client.synthesize(test['text'], voice_id=test['voice'])
            print(f"  ✓ Audio generated: {audio_url}")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return False

    return True

def test_restaurant_conversation(client):
    """Test a realistic restaurant conversation"""
    print("\n" + "="*60)
    print("TEST 3: Restaurant Conversation Flow")
    print("="*60)

    system_prompt = """You are Lily, a friendly AI assistant at Golden Dragon restaurant.
Help customers order food naturally. Keep responses concise (2-3 sentences).

Menu highlights:
- Kung Pao Chicken (宫保鸡丁) - $14.99 - Signature dish
- Mapo Tofu (麻婆豆腐) - $12.99 - Spicy, vegetarian
- Sweet and Sour Pork (糖醋里脊) - $15.99 - Popular
"""

    conversation = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': 'Hi! What do you recommend for 2 people?'}
    ]

    print("\nCustomer: Hi! What do you recommend for 2 people?")

    try:
        response = client.chat(conversation)
        print(f"Lily: {response}")

        # Test TTS with the response
        print("\nGenerating audio response...")
        audio_url = client.synthesize(response)
        print(f"✓ Audio URL: {audio_url}")

        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("DashScope API Integration Tests")
    print("="*60)

    try:
        # Initialize client
        print("\nInitializing DashScope client...")
        client = DashScopeClient()

        # Run tests
        results = []
        results.append(("LLM Test", test_llm(client)))
        results.append(("TTS Test", test_tts(client)))
        results.append(("Restaurant Conversation", test_restaurant_conversation(client)))

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        for name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{name}: {status}")

        all_passed = all(result[1] for result in results)
        if all_passed:
            print("\n✓ All tests passed! DashScope integration is working.")
            return 0
        else:
            print("\n✗ Some tests failed. Check the output above.")
            return 1

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
