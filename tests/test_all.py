#!/usr/bin/env python3
"""
All-in-one test script for streaming voice recognition
Tests everything needed to run the application
"""

import sys
import os
import subprocess

def print_header(text):
    print("\n" + "="*60)
    print(text)
    print("="*60)

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ {description}: PASS")
            if result.stdout:
                print(f"  Output: {result.stdout.strip()[:100]}")
            return True
        else:
            print(f"✗ {description}: FAIL")
            if result.stderr:
                print(f"  Error: {result.stderr.strip()[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ {description}: TIMEOUT")
        return False
    except Exception as e:
        print(f"✗ {description}: ERROR - {e}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {filepath}")
    return exists

def main():
    print_header("CamareraI - Complete System Check")

    all_tests = []

    # Test 1: Check files
    print_header("File System Check")
    files_ok = True
    files_ok &= check_file_exists("streaming_voice_agent.py", "Streaming server")
    files_ok &= check_file_exists("static/app_streaming.js", "Streaming client")
    files_ok &= check_file_exists("templates/index_streaming.html", "Streaming UI")
    files_ok &= check_file_exists("dashscope_client.py", "DashScope client")
    files_ok &= check_file_exists(".env", "Environment config")
    files_ok &= check_file_exists("data/menu.json", "Menu data")
    all_tests.append(("Files", files_ok))

    # Test 2: Check Python packages
    print_header("Python Packages Check")
    packages = [
        ("dashscope", "DashScope SDK"),
        ("flask", "Flask"),
        ("flask_socketio", "Flask-SocketIO"),
        ("dotenv", "Python-dotenv")
    ]

    packages_ok = True
    for module, name in packages:
        try:
            __import__(module)
            print(f"✓ {name}: installed")
        except ImportError:
            print(f"✗ {name}: NOT installed")
            print(f"  Install with: pip install {module}")
            packages_ok = False

    all_tests.append(("Packages", packages_ok))

    # Test 3: Network connectivity
    print_header("Network Connectivity Check")

    # DNS test
    dns_ok = run_command(
        "python3 -c \"import socket; print(socket.gethostbyname('dashscope.aliyuncs.com'))\"",
        "DNS resolution"
    )
    all_tests.append(("DNS", dns_ok))

    # Test 4: API Key
    print_header("API Key Check")
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv('DASHSCOPE_API_KEY')
    api_key_ok = bool(api_key and api_key.startswith('sk-'))

    if api_key_ok:
        print(f"✓ API key configured: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("✗ API key not configured or invalid")

    all_tests.append(("API Key", api_key_ok))

    # Test 5: DashScope API (only if previous tests pass)
    if all(result for _, result in all_tests):
        print_header("DashScope API Check")
        try:
            import dashscope
            from dashscope import Generation

            dashscope.api_key = api_key

            print("\nTesting API call...")
            response = Generation.call(
                model='qwen-turbo',
                messages=[{'role': 'user', 'content': 'Hello'}],
                result_format='message'
            )

            if response.status_code == 200:
                print("✓ DashScope API: PASS")
                print(f"  Response: {response.output.choices[0].message.content[:50]}...")
                all_tests.append(("DashScope API", True))
            else:
                print(f"✗ DashScope API: FAIL - {response.message}")
                all_tests.append(("DashScope API", False))
        except Exception as e:
            print(f"✗ DashScope API: ERROR - {e}")
            all_tests.append(("DashScope API", False))
    else:
        print_header("DashScope API Check")
        print("⚠️  Skipping (prerequisites failed)")
        all_tests.append(("DashScope API", False))

    # Summary
    print_header("Summary")

    for name, passed in all_tests:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")

    all_passed = all(result for _, result in all_tests)

    print("\n" + "="*60)

    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\n🎉 Your system is ready!")
        print("\nNext steps:")
        print("  1. Start the streaming server:")
        print("     python3 streaming_voice_agent.py")
        print("\n  2. Open your browser:")
        print("     http://localhost:5002")
        print("\n  3. Click 'Tap to Talk' and start speaking!")
        print("\n" + "="*60)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        print("\n⚠️  Please fix the issues above.")
        print("\nCommon fixes:")

        if not all_tests[0][1]:  # Files
            print("\n  Files missing:")
            print("    - Make sure you're in the correct directory")
            print("    - Run: ls -la to see files")

        if not all_tests[1][1]:  # Packages
            print("\n  Packages missing:")
            print("    - Run: pip install flask-socketio python-socketio eventlet dashscope flask python-dotenv")

        if not all_tests[2][1]:  # DNS
            print("\n  DNS resolution failed:")
            print("    - Change DNS to 8.8.8.8:")
            print("      sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4")
            print("    - Or disable VPN temporarily")

        if not all_tests[3][1]:  # API Key
            print("\n  API key issue:")
            print("    - Check .env file exists")
            print("    - Verify DASHSCOPE_API_KEY=sk-...")

        print("\n" + "="*60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
