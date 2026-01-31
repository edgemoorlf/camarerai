"""
DashScope API Client Wrapper
Handles ASR (Speech Recognition), LLM (Text Generation), and TTS (Speech Synthesis)
Updated for latest DashScope SDK (v1.24.6+)
"""

import os
from http import HTTPStatus
import dashscope
from dashscope.audio.asr import Transcription
from dashscope import Generation
from dashscope import MultiModalConversation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DashScopeClient:
    """Unified client for all DashScope services"""

    def __init__(self, api_key=None):
        """
        Initialize DashScope client

        Args:
            api_key: DashScope API key (defaults to DASHSCOPE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("DashScope API key not found. Set DASHSCOPE_API_KEY environment variable.")

        dashscope.api_key = self.api_key
        print(f"✓ DashScope client initialized")

    def transcribe(self, audio_file_url, language_hints=None):
        """
        ASR: Convert audio to text using Paraformer

        Args:
            audio_file_url: URL or path to audio file
            language_hints: List of language codes ['zh', 'en', 'yue'] for Mandarin, English, Cantonese

        Returns:
            Transcribed text string
        """
        try:
            # Submit async transcription task
            task_response = Transcription.async_call(
                model='paraformer-v2',
                file_urls=[audio_file_url],
                language_hints=language_hints or ['zh', 'en']
            )

            # Wait for task completion
            transcribe_response = Transcription.wait(task=task_response.output.task_id)

            if transcribe_response.status_code == HTTPStatus.OK:
                # Extract text from response
                results = transcribe_response.output.get('results', [])
                if results:
                    transcripts = results[0].get('transcripts', [])
                    if transcripts:
                        text = transcripts[0].get('text', '')
                        return text
                return ''
            else:
                raise Exception(f"ASR failed: {transcribe_response.message}")

        except Exception as e:
            print(f"✗ Transcription error: {e}")
            raise

    def chat(self, messages, model='qwen-plus', stream=False):
        """
        LLM: Generate response using Qwen

        Args:
            messages: List of message dicts [{'role': 'user', 'content': '...'}]
            model: Model name ('qwen-max', 'qwen-plus', 'qwen-turbo')
            stream: Whether to stream the response

        Returns:
            Generated text response (or generator if stream=True)
        """
        try:
            response = Generation.call(
                model=model,
                messages=messages,
                result_format='message',
                stream=stream
            )

            if stream:
                # Return generator for streaming
                return response
            else:
                # Return single response
                if response.status_code == HTTPStatus.OK:
                    return response.output.choices[0].message.content
                else:
                    raise Exception(f"LLM failed: {response.message}")

        except Exception as e:
            print(f"✗ Chat error: {e}")
            raise

    def synthesize(self, text, voice='Cherry', language_type='Auto', stream=False):
        """
        TTS: Convert text to speech using Qwen TTS

        Args:
            text: Text to synthesize
            voice: Voice ID (e.g., 'Cherry', 'Dylan', 'Jada', 'Sunny', 'Ethan', etc.)
            language_type: Language type ('Chinese', 'English', 'Auto', etc.)
            stream: Whether to stream the audio response

        Returns:
            Audio URL (non-streaming) or streaming response generator (streaming)
        """
        try:
            response = MultiModalConversation.call(
                model='qwen3-tts-flash',
                text=text,
                voice=voice,
                language_type=language_type,
                api_key=self.api_key,
                stream=stream
            )

            if stream:
                # Return generator for streaming
                return response
            else:
                # Return audio URL for non-streaming
                if response.status_code == HTTPStatus.OK:
                    return response.output.get('audio_url')
                else:
                    raise Exception(f"TTS failed: {response.message}")

        except Exception as e:
            print(f"✗ Synthesis error: {e}")
            raise

    def synthesize_realtime(self, text, voice='Cherry', callback=None):
        """
        TTS Realtime: Convert text to speech using Qwen TTS Realtime
        
        Note: This requires the qwen_tts_realtime module and WebSocket support.
        For simple use cases, use the synthesize() method instead.

        Args:
            text: Text to synthesize
            voice: Voice ID
            callback: Custom callback for handling real-time events

        Returns:
            Real-time TTS session (requires custom implementation)
        """
        raise NotImplementedError(
            "Real-time TTS requires WebSocket implementation. "
            "Use synthesize() method for simple TTS, or implement "
            "QwenTtsRealtime with QwenTtsRealtimeCallback for streaming."
        )

    def clone_voice(self, audio_sample_path, voice_name='custom_voice'):
        """
        Clone voice from audio sample
        
        Note: Voice cloning is available through the Qwen TTS voice design API.
        This requires additional setup and is not included in the basic SDK.

        Args:
            audio_sample_path: Path to audio sample (30-60 seconds recommended)
            voice_name: Name for the cloned voice

        Returns:
            Voice ID for the cloned voice
        """
        raise NotImplementedError(
            "Voice cloning requires Qwen TTS voice design API. "
            "Please refer to DashScope documentation for voice design: "
            "https://www.alibabacloud.com/help/en/model-studio/qwen-tts-voice-design"
        )


if __name__ == '__main__':
    # Quick test
    print("Testing DashScope client...")
    client = DashScopeClient()
    print("✓ Client initialized successfully")
    
    # Test chat
    print("\nTesting chat...")
    try:
        response = client.chat(
            messages=[{'role': 'user', 'content': 'Say hello in one sentence'}],
            model='qwen-turbo'
        )
        print(f"Chat response: {response}")
    except Exception as e:
        print(f"Chat test failed: {e}")