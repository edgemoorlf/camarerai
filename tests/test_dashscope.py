#!/usr/bin/env python3
"""Test if a DashScope key works with the Anthropic-compatible endpoint (as Claude Code would use it)."""

import sys
import json
import urllib.request
import urllib.error

DASHSCOPE_KEY = "your-dashscope-key-here"  # Replace or pass as CLI arg
BASE_URL = "https://dashscope-intl.aliyuncs.com/apps/anthropic"
MODEL = "qwen3-coder-plus"

def test_anthropic_compat(api_key: str):
    url = f"{BASE_URL}/v1/messages"
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Say hi"}]
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST"
    )

    print(f"Testing endpoint: {url}")
    print(f"Model: {MODEL}")
    print(f"Key (last 6): ...{api_key[-6:]}\n")

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
            print("✅ SUCCESS — Anthropic-compatible endpoint works!")
            print(f"Response: {body.get('content', body)}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ FAILED — HTTP {e.code}")
        print(f"Response: {body}")

        code = e.code
        try:
            err = json.loads(body).get("error", {})
            msg = err.get("message", "")
            err_code = err.get("code", "")
        except Exception:
            msg, err_code = body, ""

        print("\n--- Diagnosis ---")
        if code == 401:
            print("• Key is invalid or expired for this endpoint.")
            print("• Make sure you're using an 'international' DashScope key (dashscope-intl.aliyuncs.com)")
            print("• Domestic CN keys won't work on the intl endpoint.")
        elif code == 403:
            print("• Key is valid but lacks permission for the Anthropic-compat API.")
            print("• You may need to enable 'Anthropic model access' in your DashScope console.")
        elif code == 404:
            print(f"• Model '{MODEL}' not found or not enabled on your account.")
        elif code == 429:
            print("• Rate limit or quota exceeded.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else DASHSCOPE_KEY
    success = test_anthropic_compat(key)
    sys.exit(0 if success else 1)