"""
DashScope Service
Handles LLM (Text Generation) and TTS (Speech Synthesis)
Used by DashScope provider for streaming voice interactions
"""

import os
from http import HTTPStatus
import dashscope
from dashscope import Generation
from dashscope import MultiModalConversation


class DashScopeService:
    """Service for DashScope LLM and TTS"""

    def __init__(self, api_key=None):
        """
        Initialize DashScope service

        Args:
            api_key: DashScope API key (defaults to DASHSCOPE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("DashScope API key not found. Set DASHSCOPE_API_KEY environment variable.")

        dashscope.api_key = self.api_key

    def chat(self, messages, model='qwen-turbo', stream=False):
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
            print(f"[TTS] Synthesizing: {text[:50]}... (voice: {voice}, stream: {stream})")

            response = MultiModalConversation.call(
                model='qwen3-tts-flash',
                text=text,
                voice=voice,
                language_type=language_type,
                api_key=self.api_key,
                stream=stream,
                incremental_output=stream  # Enable incremental output for streaming
            )

            if stream:
                # Return generator for streaming audio chunks
                print(f"[TTS] Streaming mode enabled")
                return self._stream_audio_chunks(response)
            else:
                # Return audio URL for non-streaming
                if response.status_code == HTTPStatus.OK:
                    # Audio URL is nested in response.output['audio']['url']
                    audio_data = response.output.get('audio', {})
                    audio_url = audio_data.get('url') if isinstance(audio_data, dict) else None
                    print(f"[TTS] Audio URL: {audio_url}")
                    return audio_url
                else:
                    raise Exception(f"TTS failed: {response.message}")

        except Exception as e:
            print(f"✗ Synthesis error: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _stream_audio_chunks(self, response_generator):
        """
        Process streaming TTS response and yield audio chunks

        Args:
            response_generator: Streaming response from MultiModalConversation.call

        Yields:
            Audio data chunks (base64 encoded or raw bytes)
        """
        try:
            chunk_count = 0
            for chunk in response_generator:
                if chunk.status_code == HTTPStatus.OK:
                    # Extract audio data from chunk
                    if hasattr(chunk, 'output') and chunk.output:
                        audio_data = chunk.output.get('audio', {})

                        # Check for audio URL (some chunks may have URL)
                        if isinstance(audio_data, dict) and 'url' in audio_data:
                            audio_url = audio_data.get('url')
                            if audio_url:
                                chunk_count += 1
                                yield {'type': 'url', 'data': audio_url}

                        # Check for raw audio data (base64 or bytes)
                        elif isinstance(audio_data, dict) and 'data' in audio_data:
                            audio_chunk = audio_data.get('data')
                            if audio_chunk:
                                chunk_count += 1
                                yield {'type': 'data', 'data': audio_chunk}

                        # Check if audio_data itself is the data
                        elif audio_data and not isinstance(audio_data, dict):
                            chunk_count += 1
                            yield {'type': 'data', 'data': audio_data}
                else:
                    print(f"[TTS] Chunk error: {chunk.status_code} - {chunk.message}")

            print(f"[TTS] Streaming complete: {chunk_count} chunks")

        except Exception as e:
            print(f"[TTS] Streaming error: {e}")
            raise