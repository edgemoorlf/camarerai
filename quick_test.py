#!/usr/bin/env python3
"""
Quick test script to verify DashScope API connection
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_key():
    """Check if API key is configured"""
    api_key = os.getenv('DASHSCOPE_API_KEY')

    if not api_key:
        print("❌ DASHSCOPE_API_KEY not found in .env file")
        return False

    if not api_key.startswith('sk-'):
        print("⚠️  API key format looks incorrect (should start with 'sk-')")
        return False

    print(f"✓ API key found: {api_key[:10]}...{api_key[-4:]}")
    return True

def test_import():
    """Check if dashscope package is installed"""
    try:
        import dashscope
        # Try to get version, but don't fail if not available
        try:
            version = dashscope.__version__
            print(f"✓ dashscope package installed (version: {version})")
        except AttributeError:
            print(f"✓ dashscope package installed")
        return True
    except ImportError:
        print("❌ dashscope package not installed")
        print("   Run: pip install dashscope")
        return False

def test_simple_llm():
    """Test a simple LLM call"""
    try:
        import dashscope
        from dashscope import Generation

        api_key = os.getenv('DASHSCOPE_API_KEY')
        dashscope.api_key = api_key

        print("\nTesting LLM (Qwen-Plus)...")
        response = Generation.call(
            model='qwen-plus',
            messages=[{'role': 'user', 'content': 'Say hello in English, Chinese, and Cantonese'}],
            result_format='message'
        )

        if response.status_code == 200:
            content = response.output.choices[0].message.content
            print(f"✓ LLM test passed!")
            print(f"  Response: {content[:100]}...")
            return True
        else:
            print(f"❌ LLM test failed: {response.message}")
            return False

    except Exception as e:
        print(f"❌ LLM test error: {e}")
        return False

def main():
    print("="*60)
    print("DashScope Quick Test")
    print("="*60)

    results = []

    # Test 1: API Key
    print("\n[1/3] Checking API key...")
    results.append(test_api_key())

    # Test 2: Package Import
    print("\n[2/3] Checking dashscope package...")
    results.append(test_import())

    # Test 3: Simple LLM Call
    if all(results):
        print("\n[3/3] Testing API connection...")
        results.append(test_simple_llm())
    else:
        print("\n[3/3] Skipping API test (prerequisites failed)")
        results.append(False)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if all(results):
        print("✓ All tests passed! You're ready to run the application.")
        print("\nNext steps:")
        print("  1. Run: python3 poc_voice_agent.py")
        print("  2. Open: http://localhost:5000")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    exit(main())
