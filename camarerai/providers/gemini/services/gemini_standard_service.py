"""
Gemini Standard API Service
Uses Gemini 1.5 Flash for ASR + LLM (not Live API)
Matches the architecture of the working camarerai_gemini project
"""

import os
import json
import base64
from typing import Callable, Optional
from google import genai
from google.genai import types
from camarerai import config


class GeminiStandardService:
    """
    Service for Gemini Standard API integration.

    Architecture:
    1. Receives audio blob (WebM/PCM)
    2. Sends to Gemini 1.5 Flash for ASR + LLM
    3. Returns text response
    4. TTS is handled separately (by DashScope or other)

    This matches the working camarerai_gemini project pattern.
    """

    def __init__(self, perf_monitor=None):
        """
        Initialize Gemini Standard Service

        Args:
            perf_monitor: PerformanceMetrics instance for timing
        """
        self.api_key = config.GEMINI_API_KEY
        self.model = 'gemini-1.5-flash'  # Standard model, not Live API
        self.perf_monitor = perf_monitor

        # Initialize the Gemini client
        self.client = genai.Client(api_key=self.api_key)

        # System instruction for restaurant ordering
        self.system_instruction = """You are 'Lily', a helpful interactive waiter at a Chinese restaurant.
Your goal is to help customers order food, explain the menu, and share cultural context.
You must reply in the SAME language the user speaks (English, Mandarin, or Cantonese).
Your response must be a JSON object with this structure:
{
  "text": "Your helpful response here...",
  "language_code": "en-US"
}
For language_code, use:
- "en-US" for English
- "cmn-CN" for Mandarin Chinese
- "yue-HK" for Cantonese

DO NOT include markdown code blocks. Just the raw JSON object.
Keep responses concise (1-2 sentences conversational).
If the user is ordering food, acknowledge their order clearly.
"""

    def process_audio(self, audio_bytes: bytes, mime_type: str = 'audio/webm',
                      session=None, menu_data=None) -> dict:
        """
        Process audio input and return text response

        Args:
            audio_bytes: Raw audio bytes (WebM, WAV, etc.)
            mime_type: MIME type of audio (default: audio/webm)
            session: Optional session data for context
            menu_data: Optional menu data

        Returns:
            dict: {"text": str, "language_code": str}
        """
        try:
            if self.perf_monitor:
                self.perf_monitor.mark_event('gemini_api_start')

            # Build menu context if available
            menu_context = ""
            if menu_data and isinstance(menu_data, dict):
                menu_items = menu_data.get('menu', {})
                if menu_items:
                    menu_context = "\n\nAvailable menu items:\n"
                    for category, items in list(menu_items.items())[:3]:
                        menu_context += f"\n{category}:\n"
                        for item in items[:5]:
                            name = item.get('name', {})
                            if isinstance(name, dict):
                                name_str = f"{name.get('en', '')} ({name.get('zh', '')})"
                            else:
                                name_str = name
                            price = item.get('price', 0)
                            menu_context += f"  - {name_str}: ${price}\n"

            # Prepare system instruction with context
            full_system_instruction = self.system_instruction + menu_context

            # Encode audio to base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            print(f"[Gemini] Sending audio ({len(audio_bytes)} bytes, {mime_type}) to Gemini...")

            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=full_system_instruction,
                    response_mime_type='application/json'
                ),
                contents=[
                    types.Content(
                        role='user',
                        parts=[
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type=mime_type,
                                    data=audio_b64
                                )
                            )
                        ]
                    )
                ]
            )

            if self.perf_monitor:
                self.perf_monitor.mark_event('gemini_api_complete')

            # Parse response
            response_text = response.text
            if not response_text:
                raise ValueError("Empty response from Gemini")

            print(f"[Gemini] Raw response: {response_text[:100]}...")

            # Clean and parse JSON
            clean_json = response_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(clean_json)

            # Validate response structure
            if 'text' not in result:
                result['text'] = response_text
            if 'language_code' not in result:
                result['language_code'] = 'en-US'

            print(f"[Gemini] Parsed: {result['text'][:50]}... ({result['language_code']})")

            return result

        except json.JSONDecodeError as e:
            print(f"[Gemini] JSON parse error: {e}")
            # Return raw text if JSON parsing fails
            return {
                'text': response_text if 'response_text' in locals() else 'Sorry, I did not understand.',
                'language_code': 'en-US'
            }
        except Exception as e:
            print(f"[Gemini] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'text': 'Sorry, there was an error processing your request.',
                'language_code': 'en-US'
            }

    def process_text(self, text: str, session=None, menu_data=None) -> dict:
        """
        Process text input and return response
        (For fallback or text-based interaction)

        Args:
            text: Text input
            session: Optional session data
            menu_data: Optional menu data

        Returns:
            dict: {"text": str, "language_code": str}
        """
        try:
            # Build menu context if available
            menu_context = ""
            if menu_data and isinstance(menu_data, dict):
                menu_items = menu_data.get('menu', {})
                if menu_items:
                    menu_context = "\n\nAvailable menu items:\n"
                    for category, items in list(menu_items.items())[:3]:
                        menu_context += f"\n{category}:\n"
                        for item in items[:5]:
                            name = item.get('name', {})
                            if isinstance(name, dict):
                                name_str = f"{name.get('en', '')} ({name.get('zh', '')})"
                            else:
                                name_str = name
                            price = item.get('price', 0)
                            menu_context += f"  - {name_str}: ${price}\n"

            full_system_instruction = self.system_instruction + menu_context

            print(f"[Gemini] Sending text: {text[:50]}...")

            response = self.client.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=full_system_instruction,
                    response_mime_type='application/json'
                ),
                contents=[
                    types.Content(
                        role='user',
                        parts=[types.Part(text=text)]
                    )
                ]
            )

            response_text = response.text
            if not response_text:
                raise ValueError("Empty response from Gemini")

            # Clean and parse JSON
            clean_json = response_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(clean_json)

            if 'text' not in result:
                result['text'] = response_text
            if 'language_code' not in result:
                result['language_code'] = 'en-US'

            return result

        except Exception as e:
            print(f"[Gemini] Text processing error: {e}")
            return {
                'text': 'Sorry, I did not understand that.',
                'language_code': 'en-US'
            }
