"""
LLM Service - Handles LLM interaction with function calling
Manages streaming responses and TTS integration
"""

import config
from streaming_utils import has_sentence_ending


class LLMService:
    """Handles LLM interaction with function calling"""

    def __init__(self, openai_client, dashscope_client, perf_monitor):
        self.openai_client = openai_client
        self.dashscope_client = dashscope_client
        self.perf_monitor = perf_monitor

    def stream_with_function_calling(self, messages, tools, voice, session_id, emit_func):
        """
        Stream LLM response with function calling

        Args:
            messages: List of conversation messages
            tools: List of tool definitions (e.g., ORDER_UPDATE_TOOL)
            voice: Voice ID for TTS
            session_id: Session identifier
            emit_func: Function to emit events (e.g., socketio.emit)

        Returns:
            tuple: (content_buffer, tool_call_buffer)
        """
        # Start performance tracking
        self.perf_monitor.start_timer('llm')
        self.perf_monitor.mark_event('llm_start')

        print(f"[LLM] Starting streaming with qwen-turbo")

        # Stream with function calling using OpenAI-compatible API
        stream = self.openai_client.chat.completions.create(
            model='qwen-turbo',
            messages=messages,
            tools=tools,
            tool_choice='auto',
            stream=True
        )

        # Track streaming data
        content_buffer = ""
        sentence_buffer = ""
        tool_call_buffer = {"id": None, "name": None, "arguments": ""}

        # TTS tracking
        tts_call_count = 0
        sentences_sent = []

        # Notify client
        emit_func('llm_started', {'session_id': session_id})

        # LLM streaming loop - debug logging removed for performance

        for chunk in stream:
            delta = chunk.choices[0].delta

            # Handle conversational text (stream to TTS)
            if delta.content:
                # Mark first LLM token
                if not content_buffer:
                    self.perf_monitor.mark_event('llm_first_chunk')
                    llm_first_token = self.perf_monitor.calculate_duration('llm_start', 'llm_first_chunk')
                    if llm_first_token:
                        print(f"[Perf] LLM first token in {llm_first_token:.0f}ms")

                content_buffer += delta.content
                sentence_buffer += delta.content

                # Send to client for display
                emit_func('llm_chunk', {
                    'session_id': session_id,
                    'text': delta.content
                })

                # Check for sentence ending
                has_ending = has_sentence_ending(sentence_buffer)

                if has_ending:
                    tts_call_count += 1
                    sentence_to_send = sentence_buffer.strip()
                    sentences_sent.append(sentence_to_send)

                    print(f"[LLM→TTS] Sending sentence #{tts_call_count}: {sentence_to_send[:50]}...")

                    self._stream_to_tts(sentence_buffer, voice, session_id, emit_func, tts_call_count)

                    sentence_buffer = ""

            # Handle tool calls (for order updates)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.id:
                        tool_call_buffer["id"] = tc.id
                    if tc.function.name:
                        tool_call_buffer["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_call_buffer["arguments"] += tc.function.arguments

        # Process any remaining sentence

        if sentence_buffer.strip():
            tts_call_count += 1
            sentence_to_send = sentence_buffer.strip()
            sentences_sent.append(sentence_to_send)

            self._stream_to_tts(sentence_buffer, voice, session_id, emit_func, tts_call_count, is_final=True)

        print(f"[LLM] Streaming complete. Total TTS calls: {tts_call_count}")

        return content_buffer, tool_call_buffer

    def _stream_to_tts(self, text, voice, session_id, emit_func, tts_call_number, is_final=False):
        """
        Stream text to TTS

        Args:
            text: Text to synthesize
            voice: Voice ID for TTS
            session_id: Session identifier
            emit_func: Function to emit events
            tts_call_number: Sequential number of this TTS call
            is_final: Whether this is the final sentence
        """
        sentence = text.strip()[:config.MAX_TTS_LENGTH]

        # Mark TTS start
        if not is_final:
            self.perf_monitor.mark_event('tts_start')

        # Notify TTS starting
        emit_func('synthesis_started', {'session_id': session_id})

        # Stream to TTS
        try:
            first_audio_chunk = True
            chunk_count = 0

            # Starting DashScope synthesize call

            for audio_chunk in self.dashscope_client.synthesize(
                sentence,
                voice=voice,
                language_type='Auto',
                stream=True
            ):
                if first_audio_chunk and not is_final:
                    self.perf_monitor.mark_event('first_audio')
                    first_audio_time = self.perf_monitor.calculate_duration('tts_start', 'first_audio')
                    if first_audio_time:
                        print(f"[Perf] First audio in {first_audio_time:.0f}ms")
                    first_audio_chunk = False

                chunk_count += 1

                emit_func('audio_chunk', {
                    'session_id': session_id,
                    'chunk_type': audio_chunk['type'],
                    'audio_data': audio_chunk['data'],
                    'chunk_number': chunk_count,
                    'is_final': False
                })

            # Send final marker
            emit_func('audio_chunk', {
                'session_id': session_id,
                'is_final': True
            })

            sentence_type = "Final" if is_final else "Sentence"
            print(f"[TTS] {sentence_type} complete: {chunk_count} chunks")

        except Exception as e:
            print(f"[TTS] Streaming error: {e}")
