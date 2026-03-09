"""
Gemini Live API Service
Handles bidirectional audio streaming with Gemini Live API
Unified ASR + LLM + TTS in a single WebSocket connection
"""

import json
import base64
import asyncio
from typing import Callable
from google import genai
from google.genai import types
import config


class GeminiLiveService:
    """
    Service for Gemini Live API integration.

    Provides bidirectional audio streaming:
    - Sends audio chunks from client to Gemini
    - Receives audio chunks and function calls from Gemini
    - Handles order updates via function calling
    """

    def __init__(self, perf_monitor=None):
        """
        Initialize Gemini Live Service

        Args:
            perf_monitor: PerformanceMetrics instance for timing
        """
        self.api_key = config.GEMINI_API_KEY
        self.model = config.GEMINI_LIVE_MODEL
        self.perf_monitor = perf_monitor

        # Use the native Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.session = None

        self.session_id = None
        self.emit_func = None
        self.order_service = None

        # Audio format settings
        self.input_sample_rate = 16000  # 16kHz for input
        self.output_sample_rate = 24000  # 24kHz for output

        # State
        self.is_connected = False
        self.receive_task = None
        self._chunk_count = 0
        self.audio_queue = asyncio.Queue()
        self.current_session = None

    async def connect(self, session_id: str, emit_func: Callable, order_service=None, tools=None):
        """
        Establish connection to Gemini Live API using native SDK

        Args:
            session_id: Unique session identifier
            emit_func: Function to emit events to client (e.g., socketio.emit)
            order_service: OrderService instance for handling order updates
            tools: List of function definitions for Gemini
        """
        self.session_id = session_id
        self.emit_func = emit_func
        self.order_service = order_service

        try:
            print(f"[Gemini Live] Connecting using model: {self.model}")

            # Convert tools to Gemini format
            gemini_tools = self._convert_tools_to_gemini_format(tools) if tools else None

            # Create Live Connect config with audio output
            config_obj = types.LiveConnectConfig(
                response_modalities=['AUDIO'],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Aoede')
                    )
                ),
                tools=gemini_tools
            )

            # Store session for later use
            self.session = self.client.aio.live.connect(model=self.model, config=config_obj)

            print(f"[Gemini Live] Connected successfully")
            self.is_connected = True

            # Notify client
            emit_func('gemini_connected', {'session_id': session_id})

            if self.perf_monitor:
                self.perf_monitor.mark_event('gemini_connected')

        except Exception as e:
            print(f"[Gemini Live] Connection failed: {e}")
            self.is_connected = False
            raise

    def _convert_tools_to_gemini_format(self, tools):
        """
        Convert tools from OpenAI format to Gemini format

        Args:
            tools: List of tools in OpenAI format

        Returns:
            list: Tools in Gemini format
        """
        gemini_tools = []

        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                gemini_tool = types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=func.get("name"),
                            description=func.get("description"),
                            parameters=func.get("parameters", {})
                        )
                    ]
                )
                gemini_tools.append(gemini_tool)

        return gemini_tools

    async def send_audio(self, audio_data: bytes):
        """
        Send audio chunk to Gemini Live API via queue

        Args:
            audio_data: Raw audio bytes (PCM 16-bit, 16kHz)
        """
        if not self.is_connected:
            return

        try:
            # Put audio into the queue for the send loop to process
            await self.audio_queue.put(audio_data)
        except Exception as e:
            print(f"[Gemini Live] Send audio error: {e}")

    async def run_session(self):
        """
        Main session loop - receives audio and function calls from Gemini
        This should be run inside the async with session context
        """
        self.current_session = None
        try:
            async with self.session as session:
                self.current_session = session
                # Start tasks for receiving and sending
                receive_task = asyncio.create_task(self._receive_loop(session))
                send_task = asyncio.create_task(self._send_loop(session))

                # Wait for either task to complete
                done, pending = await asyncio.wait(
                    [receive_task, send_task],
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel remaining tasks
                for task in pending:
                    task.cancel()

        except Exception as e:
            print(f"[Gemini Live] Session error: {e}")
        finally:
            self.is_connected = False
            self.current_session = None

    async def _receive_loop(self, session):
        """Receive messages from Gemini"""
        try:
            async for message in session.receive():
                    # Handle audio output
                    if message.server_content and message.server_content.model_turn:
                        for part in message.server_content.model_turn.parts:
                            if part.inline_data:
                                audio_bytes = part.inline_data.data
                                self._chunk_count += 1

                                # Emit audio chunk to client
                                self.emit_func('audio_chunk', {
                                    'session_id': self.session_id,
                                    'chunk_type': 'data',
                                    'audio_data': audio_bytes,
                                    'chunk_number': self._chunk_count,
                                    'is_final': False
                                })

                                # Mark first audio for performance
                                if self._chunk_count == 1 and self.perf_monitor:
                                    self.perf_monitor.mark_event('first_audio')
                                    first_audio_time = self.perf_monitor.calculate_duration(
                                        'gemini_connected', 'first_audio'
                                    )
                                    if first_audio_time:
                                        print(f"[Perf] Gemini first audio in {first_audio_time:.0f}ms")

                            if part.text:
                                print(f"[Gemini Live] Text: {part.text[:50]}...")

                    # Handle turn completion
                    if message.server_content and message.server_content.turn_complete:
                        self.emit_func('audio_chunk', {
                            'session_id': self.session_id,
                            'is_final': True
                        })
                        print(f"[Gemini Live] Turn complete")

                    # Handle function calls
                    if message.tool_call:
                        await self._handle_tool_call(message.tool_call, session)

        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            print(f"[Gemini Live] Receive error: {e}")

    async def _send_loop(self, session):
        """Send audio messages to Gemini from queue"""
        try:
            while True:
                # Wait for audio data from the queue
                audio_data = await self.audio_queue.get()

                # Send to Gemini using realtime_input with 'media' parameter
                await session.send_realtime_input(
                    media=types.Blob(
                        mime_type='audio/pcm;rate=16000',
                        data=audio_data
                    )
                )
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            print(f"[Gemini Live] Send error: {e}")

    async def _handle_tool_call(self, tool_call, session):
        """
        Handle function calls from Gemini

        Args:
            tool_call: Tool call data from Gemini
            session: Active Live session
        """
        print(f"[Gemini Live] Tool call received")

        if not self.order_service:
            print("[Gemini Live] No order service available")
            return

        # Extract function calls
        function_calls = tool_call.function_calls

        results = []
        for call in function_calls:
            name = call.name
            args = dict(call.args) if call.args else {}
            call_id = call.id

            print(f"[Gemini Live] Function: {name}, Args: {args}")

            try:
                # Execute function
                if name == "update_order":
                    # Convert to our format
                    tool_call_buffer = {
                        "id": call_id,
                        "name": name,
                        "arguments": json.dumps(args)
                    }

                    # Process through order service
                    result = self.order_service.process_tool_call(
                        tool_call_buffer,
                        session=self._get_session(),
                        menu_data=self._get_menu_data()
                    )

                    results.append({
                        "id": call_id,
                        "result": result
                    })

                    # Emit order update to client
                    self.emit_func('order_update', {
                        'session_id': self.session_id,
                        'order': result.get('order', {}),
                        'action': result.get('action', 'unknown')
                    })

            except Exception as e:
                print(f"[Gemini Live] Function execution error: {e}")
                results.append({
                    "id": call_id,
                    "error": str(e)
                })

        # Send results back to Gemini
        await self._send_tool_results(results, session)

    async def _send_tool_results(self, results, session):
        """
        Send function results back to Gemini

        Args:
            results: List of function results
            session: Active Live session
        """
        try:
            # Convert results to Gemini format
            responses = [
                types.FunctionResponse(
                    id=result["id"],
                    response=result.get("result", {})
                )
                for result in results
            ]

            await session.send_tool_response(
                function_responses=responses
            )
        except Exception as e:
            print(f"[Gemini Live] Send tool results error: {e}")

    def _get_session(self):
        """Get current session from voice_agent (placeholder)"""
        return getattr(self, '_session', {})

    def _get_menu_data(self):
        """Get menu data (placeholder)"""
        return getattr(self, '_menu_data', {})

    def set_session_data(self, session, menu_data):
        """Set session and menu data for order processing"""
        self._session = session
        self._menu_data = menu_data

    async def disconnect(self):
        """Disconnect from Gemini Live API"""
        self.is_connected = False

        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        self.session = None
        print("[Gemini Live] Disconnected")

    def is_active(self):
        """Check if connection is active"""
        return self.is_connected and self.session is not None
