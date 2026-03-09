"""
Gemini Live API Service
Handles bidirectional audio streaming with Gemini Live API
Unified ASR + LLM + TTS in a single WebSocket connection
"""

import json
import base64
import asyncio
import websockets
from typing import Callable
import config


class GeminiLiveService:
    """
    Service for Gemini Live API integration.

    Provides bidirectional audio streaming:
    - Sends audio chunks from client to Gemini
    - Receives audio chunks and function calls from Gemini
    - Handles order updates via function calling

    Uses WebSocket connection to Google's Live API.
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

        self.websocket = None
        self.session_id = None
        self.emit_func = None
        self.order_service = None

        # Audio format settings
        self.input_sample_rate = 16000  # 16kHz for input
        self.output_sample_rate = 24000  # 24kHz for output

        # State
        self.is_connected = False
        self.receive_task = None

    async def connect(self, session_id: str, emit_func: Callable, order_service=None, tools=None):
        """
        Establish WebSocket connection to Gemini Live API

        Args:
            session_id: Unique session identifier
            emit_func: Function to emit events to client (e.g., socketio.emit)
            order_service: OrderService instance for handling order updates
            tools: List of function definitions for Gemini
        """
        self.session_id = session_id
        self.emit_func = emit_func
        self.order_service = order_service

        # Build WebSocket URL
        ws_url = (
            f"wss://generativelanguage.googleapis.com/v1alpha/models/{self.model}:connect"
            f"?key={self.api_key}"
        )

        # Prepare setup message with tools
        setup_message = self._build_setup_message(tools)

        try:
            print(f"[Gemini Live] Connecting to {self.model}...")

            self.websocket = await websockets.connect(ws_url)
            self.is_connected = True

            # Send setup configuration
            await self.websocket.send(json.dumps(setup_message))

            # Start receive loop
            self.receive_task = asyncio.create_task(self._receive_loop())

            print(f"[Gemini Live] Connected successfully")

            # Notify client
            self.emit_func('gemini_connected', {'session_id': session_id})

            if self.perf_monitor:
                self.perf_monitor.mark_event('gemini_connected')

        except Exception as e:
            print(f"[Gemini Live] Connection failed: {e}")
            self.is_connected = False
            raise

    def _build_setup_message(self, tools=None):
        """
        Build the setup message for Gemini Live API

        Args:
            tools: List of function definitions

        Returns:
            dict: Setup message for Gemini
        """
        setup = {
            "setup": {
                "model": f"models/{self.model}",
                "generation_config": {
                    "response_modalities": ["AUDIO"],  # Request audio output
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": "Aoede"  # Default voice
                            }
                        }
                    }
                }
            }
        }

        # Add tools if provided
        if tools:
            # Convert tools from OpenAI format to Gemini format
            gemini_tools = self._convert_tools_to_gemini_format(tools)
            setup["setup"]["tools"] = gemini_tools

        return setup

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
                gemini_tool = {
                    "function_declarations": [
                        {
                            "name": func.get("name"),
                            "description": func.get("description"),
                            "parameters": func.get("parameters", {})
                        }
                    ]
                }
                gemini_tools.append(gemini_tool)

        return gemini_tools

    async def send_audio(self, audio_data: bytes):
        """
        Send audio chunk to Gemini Live API

        Args:
            audio_data: Raw audio bytes (PCM 16-bit, 16kHz)
        """
        if not self.is_connected or not self.websocket:
            return

        try:
            # Encode audio as base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')

            message = {
                "realtime_input": {
                    "media_chunks": [
                        {
                            "mime_type": "audio/pcm;rate=16000",
                            "data": audio_b64
                        }
                    ]
                }
            }

            await self.websocket.send(json.dumps(message))

        except Exception as e:
            print(f"[Gemini Live] Send audio error: {e}")

    async def _receive_loop(self):
        """
        Main receive loop for Gemini Live API messages
        Handles audio output and function calls
        """
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)

                    # Handle server content (audio output)
                    if "serverContent" in data:
                        await self._handle_server_content(data["serverContent"])

                    # Handle tool calls
                    elif "toolCall" in data:
                        await self._handle_tool_call(data["toolCall"])

                    # Handle setup complete
                    elif "setupComplete" in data:
                        print("[Gemini Live] Setup complete")

                    # Handle errors
                    elif "error" in data:
                        print(f"[Gemini Live] Error: {data['error']}")

                except json.JSONDecodeError:
                    print(f"[Gemini Live] Invalid JSON: {message[:100]}")

        except websockets.exceptions.ConnectionClosed:
            print("[Gemini Live] Connection closed")
        except Exception as e:
            print(f"[Gemini Live] Receive error: {e}")
        finally:
            self.is_connected = False

    async def _handle_server_content(self, content):
        """
        Handle server content (audio output from Gemini)

        Args:
            content: Server content dict
        """
        # Check for audio output
        if "output" in content and "audio" in content["output"]:
            audio_data = content["output"]["audio"]

            if "data" in audio_data:
                # Decode base64 audio
                audio_bytes = base64.b64decode(audio_data["data"])
                chunk_count = getattr(self, '_chunk_count', 0) + 1
                self._chunk_count = chunk_count

                # Emit audio chunk to client
                self.emit_func('audio_chunk', {
                    'session_id': self.session_id,
                    'chunk_type': 'data',
                    'audio_data': audio_bytes,
                    'chunk_number': chunk_count,
                    'is_final': False
                })

                # Mark first audio for performance
                if chunk_count == 1 and self.perf_monitor:
                    self.perf_monitor.mark_event('first_audio')
                    first_audio_time = self.perf_monitor.calculate_duration(
                        'gemini_connected', 'first_audio'
                    )
                    if first_audio_time:
                        print(f"[Perf] Gemini first audio in {first_audio_time:.0f}ms")

        # Check for text (if any)
        if "output" in content and "text" in content["output"]:
            text = content["output"]["text"]
            print(f"[Gemini Live] Text: {text[:50]}...")

        # Check for turn completion
        if "turnComplete" in content and content["turnComplete"]:
            # Send final marker
            self.emit_func('audio_chunk', {
                'session_id': self.session_id,
                'is_final': True
            })
            print(f"[Gemini Live] Turn complete")

    async def _handle_tool_call(self, tool_call_data):
        """
        Handle function calls from Gemini

        Args:
            tool_call_data: Tool call data from Gemini
        """
        print(f"[Gemini Live] Tool call received")

        if not self.order_service:
            print("[Gemini Live] No order service available")
            return

        # Extract function calls
        function_calls = tool_call_data.get("functionCalls", [])

        results = []
        for call in function_calls:
            name = call.get("name")
            args = call.get("args", {})
            call_id = call.get("id", "")

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
        await self._send_tool_results(results)

    async def _send_tool_results(self, results):
        """
        Send function results back to Gemini

        Args:
            results: List of function results
        """
        if not self.websocket:
            return

        message = {
            "tool_response": {
                "function_responses": [
                    {
                        "id": result["id"],
                        "response": result.get("result", {})
                    }
                    for result in results
                ]
            }
        }

        await self.websocket.send(json.dumps(message))

    def _get_session(self):
        """Get current session from voice_agent (placeholder)"""
        # This will be passed from voice_agent
        # For now, return a minimal session dict
        return getattr(self, '_session', {})

    def _get_menu_data(self):
        """Get menu data (placeholder)"""
        # This will be passed from voice_agent
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

        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        print("[Gemini Live] Disconnected")

    def is_active(self):
        """Check if connection is active"""
        return self.is_connected and self.websocket is not None
