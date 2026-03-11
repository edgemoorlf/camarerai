"""
Streaming Voice Recognition Server using WebSocket
Supports both DashScope and Gemini providers
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import uuid
import base64
from performance_monitor import PerformanceMetrics
import config
from services.order_service import OrderService
from services.provider_factory import create_order_service, get_provider_info

# ============================================================================
# Provider-Specific Initialization (Clean Separation)
# ============================================================================

provider_info = get_provider_info()
print(f"[Provider] Using provider: {provider_info['provider']}")

# Initialize performance monitoring (shared)
perf_monitor = PerformanceMetrics(max_history=config.MAX_PERFORMANCE_HISTORY)

# Initialize order service (shared)
order_service = create_order_service()

# --- DASHSCOPE ARCHITECTURE ---
if config.PROVIDER == 'dashscope':
    from services.dashscope_service import DashScopeService
    from services.llm_service import LLMService
    from openai import OpenAI
    from dashscope.audio.asr import Recognition
    import dashscope
    from asr_vocabulary import get_or_create_phrases

    # Set DashScope API key globally (required for Recognition class)
    dashscope.api_key = config.DASHSCOPE_API_KEY

    # Initialize DashScope services
    dashscope_service = DashScopeService()
    openai_client = OpenAI(
        api_key=config.DASHSCOPE_API_KEY,
        base_url=config.DASHSCOPE_BASE_URL,
        http_client=config.HTTP_CLIENT
    )
    llm_service = LLMService(openai_client, dashscope_service, perf_monitor)

    # ASR hot words support
    asr_phrase_id = None
    def init_asr_phrases():
        """Initialize ASR hot words in background"""
        global asr_phrase_id
        try:
            asr_phrase_id = get_or_create_phrases()
            if asr_phrase_id:
                print(f"[ASR] Hot words enabled: {asr_phrase_id}")
            else:
                print("[ASR] Hot words not available, using default ASR")
        except Exception as e:
            print(f"[ASR] Hot words initialization failed: {e}")
            print("[ASR] Continuing with default ASR settings")

    # Start hot words initialization
    init_asr_phrases()

    print("[Provider] DashScope architecture initialized")

# --- GEMINI ARCHITECTURE ---
elif config.PROVIDER == 'gemini':
    from services.gemini_standard_service import GeminiStandardService
    from services.dashscope_service import DashScopeService  # Only for TTS

    # Initialize Gemini service (ASR + LLM)
    gemini_service = GeminiStandardService(perf_monitor)

    # Initialize DashScope service (TTS only - Gemini doesn't have native TTS)
    dashscope_service = DashScopeService()

    # No hot words needed for Gemini (handled by model)
    asr_phrase_id = None

    print("[Provider] Gemini architecture initialized")

# --- UNKNOWN PROVIDER ---
else:
    raise ValueError(f"Unknown provider: {config.PROVIDER}. Use 'dashscope' or 'gemini'.")

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
socketio = SocketIO(app, **config.SOCKETIO_CONFIG)


# ============================================================================
# Connection Pre-warming (Performance Optimization)
# ============================================================================

def prewarm_connections():
    """
    Pre-warm API connections by sending a small request.
    This establishes HTTP connection (DNS + TCP + TLS) before user speaks,
    eliminating 80-350ms connection overhead on first real request.
    """
    import threading

    def _warmup():
        try:
            print("[Perf] Pre-warming API connections...")

            if config.PROVIDER == 'dashscope' and openai_client:
                # Warm up DashScope LLM connection with minimal request
                _ = openai_client.chat.completions.create(
                    model='qwen-plus',
                    messages=[{'role': 'user', 'content': 'hi'}],
                    max_tokens=1,
                    stream=False
                )
                print("[Perf] ✓ DashScope connections pre-warmed")
            elif config.PROVIDER == 'gemini':
                # Gemini Standard API is stateless REST
                # Connection pooling is handled by the HTTP client
                print("[Perf] ✓ Gemini Standard API ready")

        except Exception as e:
            # Non-critical - just log warning
            print(f"[Perf] Pre-warm warning: {e}")

    # Run in background thread to avoid blocking
    threading.Thread(target=_warmup, daemon=True).start()


# In-memory session storage
sessions = {}
active_recognitions = {}

# Load restaurant data
def load_json_data(filename):
    """Load JSON data from data directory"""
    filepath = os.path.join('data', filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

menu_data = load_json_data('menu.json')
knowledge_data = load_json_data('knowledge.json')
table_names = load_json_data('table_names.json')
voices_data = load_json_data('voices.json')


class ConversationSession:
    """Manages a conversation session for a table"""

    def __init__(self, table_id, role='customer'):
        self.session_id = str(uuid.uuid4())
        self.table_id = table_id
        self.table_name = self._assign_table_name()
        self.role = role
        self.language = 'en'
        self.party_size = None
        self.dietary_restrictions = []

        # Session state management
        self.state = config.SessionState.IDLE

        # Order management
        self.current_order = []        # Items being added (editable in ORDERING state)
        self.confirmed_items = []      # Items locked after confirmation
        self.order_confirmed_at = None

        # Passive listening
        self.passive_transcripts = []  # Transcripts captured in passive mode

        self.conversation_history = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.speakers = {}

    def _assign_table_name(self):
        """Assign a unique table name"""
        names = table_names.get('names', ['Lily', 'Emma', 'Sophie', 'Grace'])
        name_index = int(self.table_id) % len(names) if self.table_id.isdigit() else 0
        return f"Table {self.table_id} - {names[name_index]}"

    def add_message(self, role, content, speaker_id=None):
        """Add a message to conversation history"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'speaker_id': speaker_id
        }
        self.conversation_history.append(message)
        self.last_activity = datetime.now()
        return message

    def _is_closing_remark(self, message):
        """Check if message is a closing remark"""
        message_lower = message.lower().strip()

        # English closing remarks
        english_closings = [
            'thank you', 'thanks', "that's all", 'go ahead',
            'send the order', "that'll be all", 'thats all',
            "that's it", 'thats it'
        ]

        # Mandarin closing remarks
        mandarin_closings = [
            '谢谢', '好的', '可以了', '就这些', '下单吧',
            '没了', '够了', '行了'
        ]

        # Cantonese closing remarks
        cantonese_closings = [
            '唔該', '多謝', '得啦', '可以啦', '落單啦',
            '夠啦', '冇啦'
        ]

        # Check if message contains any closing remark
        for closing in english_closings + mandarin_closings + cantonese_closings:
            if closing in message_lower:
                return True

        return False

    def get_system_prompt(self):
        """Generate role-specific system prompt"""
        restaurant_name = menu_data.get('restaurant', {}).get('name', 'Golden Dragon')

        if self.role == 'customer':
            # Build current order summary
            order_summary = "No items yet"
            if self.current_order:
                order_items = []
                for item in self.current_order:
                    order_items.append(f"- {item['name']} x{item['quantity']} (${item['price']})")
                order_summary = '\n'.join(order_items)

            # Build passive context if available
            passive_context = ""
            if self.passive_transcripts:
                passive_context = f"""

Context from customer conversation (captured while dining):
{chr(10).join(f"- {t}" for t in self.passive_transcripts[-5:])}

Use this context to better understand customer preferences and needs.
"""

            # State-specific guidelines
            state_guidelines = ""
            if self.state == config.SessionState.CONFIRMED:
                state_guidelines = """

ORDER STATUS: The order has been CONFIRMED and locked.
- Customer CAN add MORE items (new orders)
- Customer CAN ask questions
- Customer CAN request service
- Customer CANNOT modify or remove confirmed items

If customer tries to modify/remove confirmed items, politely explain:
"Your order has been confirmed and sent to the kitchen. I can add more items, but cannot modify the confirmed order. Would you like to add something else?"
"""

            return f"""You are {self.table_name.split(' - ')[1]}, a friendly AI assistant at {restaurant_name}.
Help customers order food naturally.

CRITICAL: Respond in the SAME LANGUAGE the customer is speaking:
- If customer speaks Chinese (Mandarin/Cantonese), respond in Chinese
- If customer speaks English, respond in English
- Match their language exactly

Current context:
- Table: {self.table_name}
- Party size: {self.party_size or 'unknown'}
- Dietary restrictions: {', '.join(self.dietary_restrictions) or 'none'}
- Current order ({len(self.current_order)} items):
{order_summary}{passive_context}{state_guidelines}

Menu highlights:
{self._get_menu_summary()}

Guidelines:
- Be conversational and warm
- Ask about dietary restrictions if not known
- Suggest popular items and staff recommendations
- Confirm quantities and modifications
- Keep responses concise (2-3 sentences)
- ALWAYS respond in the customer's language
- When customer orders items, acknowledge them clearly
"""
        elif self.role == 'owner':
            return f"""You are {self.table_name.split(' - ')[1]}, assistant to the owner of {restaurant_name}.
Provide business insights and help manage the restaurant.
Speak in their language (English, Mandarin, or Cantonese).

Today's context:
- Active tables: {len(sessions)}
- Total orders: {sum(len(s.current_order) for s in sessions.values())}
"""
        else:
            return f"""You are {self.table_name.split(' - ')[1]}, assistant to the staff at {restaurant_name}.
Help with order details and table management.
Speak in their language (English, Mandarin, or Cantonese).

Current orders: {len(self.current_order)} items
"""

    def _get_menu_summary(self):
        """Get a concise menu summary"""
        menu = menu_data.get('menu', {})
        summary = []

        for category, items in menu.items():
            if items and len(items) > 0:
                top_items = items[:3]
                for item in top_items:
                    name = item.get('name', {})
                    if isinstance(name, dict):
                        name_str = f"{name.get('en', '')} ({name.get('zh', '')})"
                    else:
                        name_str = name
                    price = item.get('price', 0)
                    summary.append(f"- {name_str}: ${price}")

        return '\n'.join(summary[:10])


class StreamingRecognitionCallback:
    """Callback for streaming ASR results"""

    def __init__(self, session_id, socketio_instance, client_sid):
        self.session_id = session_id
        self.socketio = socketio_instance
        self.client_sid = client_sid
        self.completed_sentences = []  # Stores finalized sentences
        self.current_sentence = ""      # Current partial sentence

    def on_open(self):
        print(f"[ASR] Connection opened for session {self.session_id}")
        self.socketio.emit('recognition_started', {
            'session_id': self.session_id
        }, room=self.client_sid)

    def on_complete(self):
        print(f"[ASR] Recognition complete for session {self.session_id}")
        # Combine all completed sentences with current partial
        full_text = " ".join(self.completed_sentences)
        if self.current_sentence:
            full_text = (full_text + " " + self.current_sentence).strip()
        self.socketio.emit('transcription_complete', {
            'session_id': self.session_id,
            'text': full_text
        }, room=self.client_sid)

    def on_error(self, message):
        print(f"[ASR] Error for session {self.session_id}: {message}")
        self.socketio.emit('transcription_error', {
            'session_id': self.session_id,
            'error': str(message)
        }, room=self.client_sid)

    def on_close(self):
        print(f"[ASR] Connection closed for session {self.session_id}")

    def on_event(self, result):
        """Handle streaming transcription events"""
        try:
            if not result:
                return

            # Extract sentence from result
            sentence = result.get_sentence() if hasattr(result, 'get_sentence') else None

            if sentence:
                text = ''
                is_end = False

                if isinstance(sentence, dict):
                    text = sentence.get('text', '')
                    is_end = sentence.get('end', False) or sentence.get('sentence_end', False)
                elif isinstance(sentence, list) and len(sentence) > 0:
                    last_sentence = sentence[-1]
                    if isinstance(last_sentence, dict):
                        text = last_sentence.get('text', '')
                        is_end = last_sentence.get('end', False) or last_sentence.get('sentence_end', False)

                if text:
                    if is_end:
                        # Sentence is complete, add to completed list
                        self.completed_sentences.append(text)
                        self.current_sentence = ""

                        # Build full text and send transcription_complete
                        full_text = " ".join(self.completed_sentences)

                        print(f"[ASR] Sentence complete: {full_text}")

                        # Mark ASR complete for performance tracking
                        perf_monitor.mark_event('asr_complete')
                        perf_monitor.end_timer('asr')

                        # Check if session is in passive mode
                        if self.session_id in sessions:
                            session = sessions[self.session_id]

                            if session.state == config.SessionState.CONFIRMED_PASSIVE:
                                # Passive mode - capture but don't respond
                                print(f"[Passive] Captured: {full_text}")
                                session.passive_transcripts.append(full_text)
                                session.add_message('user', full_text, speaker_id=None)

                                # Send transcription but mark as passive
                                self.socketio.emit('transcription_passive', {
                                    'session_id': self.session_id,
                                    'text': full_text
                                }, room=self.client_sid)

                                # Clear completed sentences for next utterance
                                self.completed_sentences = []
                                return

                        # Normal mode - send transcription_complete to trigger chat
                        self.socketio.emit('transcription_complete', {
                            'session_id': self.session_id,
                            'text': full_text
                        }, room=self.client_sid)

                        # Clear completed sentences for next utterance
                        self.completed_sentences = []
                    else:
                        # Still building current sentence
                        self.current_sentence = text

                    # Build full text for display (completed + current)
                    display_text = " ".join(self.completed_sentences)
                    if self.current_sentence:
                        display_text = (display_text + " " + self.current_sentence).strip()

                    # Send partial result to client
                    self.socketio.emit('transcription_partial', {
                        'session_id': self.session_id,
                        'text': display_text,
                        'is_final': is_end
                    }, room=self.client_sid)

                    print(f"[ASR] Partial result: {display_text} (final: {is_end})")

        except Exception as e:
            print(f"[ASR] Event processing error: {e}")
            import traceback
            traceback.print_exc()


@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f"[WebSocket] Client connected: {request.sid}")
    emit('connected', {'status': 'ok'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f"[WebSocket] Client disconnected: {request.sid}")
    # Clean up any active recognition
    if request.sid in active_recognitions:
        try:
            rec_data = active_recognitions[request.sid]
            # Handle Gemini Standard API - just cleanup, no persistent connection
            if rec_data.get('provider') == 'gemini':
                # Gemini Standard API is stateless, just clean up the buffer
                print(f"[Gemini] Cleaning up recognition for session {rec_data.get('session_id')}")
            elif rec_data['started']:
                rec_data['recognition'].stop()
        except:
            pass
        del active_recognitions[request.sid]


@socketio.on('create_session')
def handle_create_session(data):
    """Create a new conversation session"""
    table_id = data.get('table_id', '1')
    role = data.get('role', 'customer')

    session = ConversationSession(table_id, role)
    session.state = config.SessionState.ORDERING  # Start in ORDERING state to capture orders immediately
    sessions[session.session_id] = session

    # Pre-warm connections to reduce first request latency
    prewarm_connections()

    emit('session_created', {
        'session_id': session.session_id,
        'table_name': session.table_name,
        'role': role,
        'state': session.state
    })


@socketio.on('start_recognition')
def handle_start_recognition(data):
    """Start streaming ASR (DashScope) or Gemini Standard API recognition"""
    session_id = data.get('session_id')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    try:
        session = sessions[session_id]

        # Gemini Standard API mode (batch processing)
        if config.PROVIDER == 'gemini':
            if not gemini_service:
                emit('error', {'message': 'Gemini service not available'})
                return

            # Start performance tracking
            perf_monitor.start_timer('gemini_asr')

            # Store in active recognitions for audio accumulation
            # Audio will be accumulated and sent to Gemini when recognition stops
            active_recognitions[request.sid] = {
                'audio_buffer': bytearray(),  # Accumulate audio bytes here
                'started': True,
                'session_id': session_id,
                'provider': 'gemini',
                'session': session,
                'mime_type': 'audio/webm'  # Default, will be set by client
            }

            emit('recognition_started', {
                'session_id': session_id,
                'provider': 'gemini'
            })
            print(f"[Gemini] Recognition started for session {session_id} (audio will be accumulated)")
            return

        # DashScope ASR mode
        # Start performance tracking for ASR
        perf_monitor.start_timer('asr')

        # Create callback for this recognition session
        callback = StreamingRecognitionCallback(session_id, socketio, request.sid)

        # Create streaming recognition
        recognition = Recognition(
            model='paraformer-realtime-v2',
            format='pcm',
            sample_rate=16000,
            callback=callback,
            semantic_punctuation_enabled=True,
            max_sentence_silence=5000,
            disfluency_removal_enabled=False
        )

        # Store recognition instance with metadata (don't start yet)
        active_recognitions[request.sid] = {
            'recognition': recognition,
            'started': False,
            'session_id': session_id,
            'callback': callback,
            'provider': 'dashscope'
        }

        print(f"[ASR] Recognition prepared for session {session_id}")

    except Exception as e:
        print(f"[ASR] Failed to prepare recognition: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Failed to start recognition: {str(e)}'})


@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle streaming audio data"""
    try:
        # Gemini Standard API mode - accumulate audio
        if config.PROVIDER == 'gemini':
            if request.sid not in active_recognitions:
                return

            rec_data = active_recognitions[request.sid]
            audio_base64 = data.get('audio')
            if not audio_base64:
                return

            audio_bytes = base64.b64decode(audio_base64)

            # Accumulate audio in buffer for batch processing
            rec_data['audio_buffer'].extend(audio_bytes)
            return

        # DashScope ASR mode
        if request.sid not in active_recognitions:
            return

        rec_data = active_recognitions[request.sid]
        recognition = rec_data['recognition']

        # Start recognition on first audio frame
        if not rec_data['started']:
            # Use hot words if available (improves accuracy for restaurant terms)
            if asr_phrase_id:
                recognition.start(phrase_id=asr_phrase_id)
                print(f"[ASR] Recognition started with hot words for session {rec_data['session_id']}")
            else:
                recognition.start()
                print(f"[ASR] Recognition started for session {rec_data['session_id']}")
            rec_data['started'] = True

        # Get audio data (base64 encoded)
        audio_base64 = data.get('audio')
        if not audio_base64:
            return

        # Decode audio data
        audio_bytes = base64.b64decode(audio_base64)

        # Send to recognition
        try:
            recognition.send_audio_frame(audio_bytes)
        except Exception as send_error:
            # If recognition has stopped, restart it
            if "stopped" in str(send_error).lower():
                print(f"[ASR] Recognition stopped, restarting for session {rec_data['session_id']}")

                # Create new recognition instance
                callback = StreamingRecognitionCallback(rec_data['session_id'], socketio, request.sid)
                new_recognition = Recognition(
                    model='paraformer-realtime-v2',
                    format='pcm',
                    sample_rate=16000,
                    callback=callback,
                    semantic_punctuation_enabled=True,
                    max_sentence_silence=5000,
                    disfluency_removal_enabled=False
                )

                # Start new recognition
                if asr_phrase_id:
                    new_recognition.start(phrase_id=asr_phrase_id)
                else:
                    new_recognition.start()

                # Update stored recognition
                active_recognitions[request.sid] = {
                    'recognition': new_recognition,
                    'started': True,
                    'session_id': rec_data['session_id'],
                    'callback': callback
                }

                # Send audio to new recognition
                new_recognition.send_audio_frame(audio_bytes)
                print(f"[ASR] Recognition restarted successfully")
            else:
                raise send_error

    except Exception as e:
        print(f"[ASR] Audio data error: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Audio processing error: {str(e)}'})


@socketio.on('stop_recognition')
def handle_stop_recognition(data):
    """Stop streaming ASR or Gemini Standard API"""
    try:
        if request.sid in active_recognitions:
            rec_data = active_recognitions[request.sid]

            # Handle Gemini Standard API
            if rec_data.get('provider') == 'gemini':
                # Process accumulated audio in background thread
                audio_buffer = bytes(rec_data.get('audio_buffer', bytearray()))
                session_id = rec_data['session_id']
                session = rec_data.get('session')
                client_sid = request.sid

                if len(audio_buffer) > 0 and session:
                    def process_gemini_audio():
                        try:
                            print(f"[Gemini] Processing {len(audio_buffer)} bytes of audio...")

                            # Mark ASR complete
                            if perf_monitor:
                                perf_monitor.mark_event('gemini_asr_complete')
                                asr_time = perf_monitor.calculate_duration('gemini_asr', 'gemini_asr_complete')
                                if asr_time:
                                    print(f"[Perf] Gemini ASR took {asr_time:.0f}ms")

                            # Send to Gemini for ASR + LLM
                            result = gemini_service.process_audio(
                                audio_bytes=audio_buffer,
                                mime_type='audio/webm',
                                session=session,
                                menu_data=menu_data
                            )

                            text = result.get('text', '')
                            language_code = result.get('language_code', 'en-US')

                            print(f"[Gemini] Response: {text[:100]}... (lang: {language_code})")

                            # Emit transcription
                            socketio.emit('transcription', {
                                'session_id': session_id,
                                'text': text,
                                'is_final': True,
                                'provider': 'gemini'
                            }, room=client_sid)

                            # Add to conversation history
                            session.add_message('user', text)

                            # Process with order service if needed
                            order_result = None
                            if session.state == config.SessionState.ORDERING:
                                # Check if this is an order-related message
                                order_keywords = ['order', '点', '要', 'add', 'get', 'want', 'give me']
                                if any(kw in text.lower() for kw in order_keywords):
                                    # Process as order update
                                    tool_call = {
                                        'id': f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                                        'name': 'update_order',
                                        'arguments': json.dumps({'customer_input': text})
                                    }
                                    order_result = order_service.process_tool_call(
                                        tool_call,
                                        session=session,
                                        menu_data=menu_data
                                    )
                                    # Emit order update
                                    socketio.emit('order_update', {
                                        'session_id': session_id,
                                        'order': order_result.get('order', {}),
                                        'action': order_result.get('action', 'unknown')
                                    }, room=client_sid)

                            # Now do TTS for the response
                            perf_monitor.start_timer('tts') if perf_monitor else None

                            # Stream TTS audio to client
                            tts_chunks = dashscope_service.stream_tts(text, language_code)

                            socketio.emit('tts_start', {
                                'session_id': session_id,
                                'language_code': language_code
                            }, room=client_sid)

                            chunk_count = 0
                            for chunk in tts_chunks:
                                chunk_count += 1
                                socketio.emit('audio_chunk', {
                                    'session_id': session_id,
                                    'chunk_type': 'data',
                                    'audio_data': chunk['audio_data'],
                                    'chunk_number': chunk_count,
                                    'is_final': False
                                }, room=client_sid)

                            socketio.emit('audio_chunk', {
                                'session_id': session_id,
                                'is_final': True
                            }, room=client_sid)

                            if perf_monitor:
                                perf_monitor.mark_event('tts_complete')
                                tts_time = perf_monitor.calculate_duration('tts', 'tts_complete')
                                if tts_time:
                                    print(f"[Perf] TTS took {tts_time:.0f}ms for {chunk_count} chunks")

                        except Exception as e:
                            print(f"[Gemini] Processing error: {e}")
                            import traceback
                            traceback.print_exc()
                            socketio.emit('error', {'message': f'Processing error: {str(e)}'}, room=client_sid)

                    import threading
                    threading.Thread(target=process_gemini_audio, daemon=True).start()
                else:
                    print(f"[Gemini] No audio data to process for session {session_id}")
            else:
                # Handle DashScope ASR
                recognition = rec_data['recognition']
                if rec_data['started']:
                    recognition.stop()
                    print(f"[ASR] Recognition stopped for session {rec_data['session_id']}")

            del active_recognitions[request.sid]

        emit('recognition_stopped', {'status': 'ok'})

    except Exception as e:
        print(f"[ASR] Stop recognition error: {e}")
        emit('error', {'message': f'Failed to stop recognition: {str(e)}'})


@socketio.on('chat')
def handle_chat(data):
    """Process chat message with function calling (DashScope only)"""
    session_id = data.get('session_id')
    message = data.get('message')

    # Gemini Standard API - process chat like DashScope
    if config.PROVIDER == 'gemini':
        print(f"[Chat] Processing chat via Gemini Standard API")
        # Fall through to normal chat processing below

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    session = sessions[session_id]

    try:
        # Add user message to history
        session.add_message('user', message)

        # Build messages for LLM
        system_prompt = session.get_system_prompt()

        # Build menu context
        menu_items_list = []
        menu = menu_data.get('menu', {})
        for category, items in menu.items():
            for item in items:
                name = item.get('name', {})
                if isinstance(name, dict):
                    menu_items_list.append({
                        'en': name.get('en', ''),
                        'zh': name.get('zh', ''),
                        'yue': name.get('yue', ''),
                        'price': item.get('price', 0),
                        'id': item.get('id', '')
                    })

        # State-aware function calling prompt
        if session.state == config.SessionState.ORDERING:
            function_calling_prompt = f"""
IMPORTANT: When customer orders items, you MUST do TWO things:

1. FIRST: Respond conversationally to acknowledge their order (e.g., "好的，我帮您点一份麻婆豆腐")
2. THEN: Call the update_order function with the structured order details

You MUST do BOTH steps in your response.

Available menu items:
{chr(10).join([f"- {item['en']} / {item['zh']} / {item['yue']}: ${item['price']}" for item in menu_items_list[:15]])}

Current order ({len(session.current_order)} items):
{chr(10).join([f"- {item['name']} x{item['quantity']}" for item in session.current_order]) if session.current_order else "No items yet"}

CRITICAL RULES:
1. ONLY call update_order when customer EXPLICITLY orders items
2. DO NOT call update_order when making recommendations or answering questions
3. Customer must use ordering language like "我要...", "给我...", "I'll have...", "Can I get..."
4. For removals, customer must use removal language like "取消...", "不想要...", "Cancel...", "Remove..."
5. ALWAYS call update_order for removals
"""
        elif session.state == config.SessionState.CONFIRMED:
            confirmed_summary = '\n'.join([f"- {item['name']} x{item['quantity']}" for item in session.confirmed_items]) if session.confirmed_items else "No confirmed items"

            function_calling_prompt = f"""
IMPORTANT: The order has been CONFIRMED. Customer can ONLY add MORE items.

When customer orders NEW items, you MUST do TWO things:
1. FIRST: Respond conversationally
2. THEN: Call update_order function with action "add"

You MUST do BOTH steps.

Confirmed Order (LOCKED):
{confirmed_summary}

Available menu items:
{chr(10).join([f"- {item['en']} / {item['zh']}: ${item['price']}" for item in menu_items_list[:15]])}

CRITICAL: ONLY use action "add". DO NOT use "modify" or "remove".
"""
        else:
            function_calling_prompt = ""

        messages = [
            {'role': 'system', 'content': system_prompt + '\n\n' + function_calling_prompt}
        ]

        # Add conversation history
        for msg in session.conversation_history[-10:]:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })

        # Get voice for this table
        voice = voices_data.get('tables', {}).get(session.table_id, 'Cherry')

        # Stream LLM with function calling using LLMService
        content_buffer, tool_call_buffer = llm_service.stream_with_function_calling(
            messages=messages,
            tools=[config.ORDER_UPDATE_TOOL],
            voice=voice,
            session_id=session_id,
            emit_func=emit
        )

        # Process tool call if present
        if tool_call_buffer["name"]:
            print(f"[Function Call] {tool_call_buffer['name']}")

            # Use OrderService to process the tool call
            order_result = OrderService.process_tool_call(tool_call_buffer, session)

            if order_result:
                # Send order update to client
                emit('order_updated', {
                    'session_id': session_id,
                    'confirmed_items': session.confirmed_items,
                    'current_order': session.current_order,
                    **order_result
                })

        # Check for closing remark and handle state transition
        if session._is_closing_remark(message):
            if session.state == config.SessionState.ORDERING:
                # First confirmation - lock order and enter passive mode
                session.confirmed_items.extend(session.current_order)
                session.current_order = []
                session.state = config.SessionState.CONFIRMED_PASSIVE
                session.order_confirmed_at = datetime.now()

                print(f"[Session] State transition: ORDERING → CONFIRMED_PASSIVE")
                print(f"[Session] Locked {len(session.confirmed_items)} items")

                # Calculate totals
                subtotal = sum(item['price'] * item['quantity'] for item in session.confirmed_items)
                tax = subtotal * config.TAX_RATE
                total = subtotal + tax

                # Notify client of state change
                emit('state_changed', {
                    'session_id': session_id,
                    'state': 'confirmed_passive',
                    'confirmed_items': session.confirmed_items,
                    'current_order': [],
                    'button_text': 'Tap for Anything',
                    'show_stop_button': True,
                    'subtotal': round(subtotal, 2),
                    'tax': round(tax, 2),
                    'total': round(total, 2)
                })

            elif session.state == config.SessionState.CONFIRMED:
                # Additional confirmation - lock new items and return to passive
                if session.current_order:
                    session.confirmed_items.extend(session.current_order)
                    session.current_order = []
                    session.state = config.SessionState.CONFIRMED_PASSIVE

                    print(f"[Session] Additional confirmation: CONFIRMED → CONFIRMED_PASSIVE")
                    print(f"[Session] Total locked items: {len(session.confirmed_items)}")

                    # Calculate totals
                    subtotal = sum(item['price'] * item['quantity'] for item in session.confirmed_items)
                    tax = subtotal * config.TAX_RATE
                    total = subtotal + tax

                    # Send order update
                    emit('order_updated', {
                        'session_id': session_id,
                        'confirmed_items': session.confirmed_items,
                        'current_order': [],
                        'subtotal': round(subtotal, 2),
                        'tax': round(tax, 2),
                        'total': round(total, 2)
                    })

                    # Notify state change to passive
                    emit('state_changed', {
                        'session_id': session_id,
                        'state': 'confirmed_passive',
                        'show_stop_button': True
                    })

        # End LLM timer
        perf_monitor.end_timer('llm')

        # Record metrics
        perf_monitor.record_request()
        metrics = perf_monitor.get_metrics_for_client()
        emit('performance_metrics', {
            'session_id': session_id,
            'metrics': metrics
        })

        # Add assistant response to history
        session.add_message('assistant', content_buffer)

        # Send chat response
        emit('chat_response', {
            'session_id': session_id,
            'response': content_buffer,
            'table_name': session.table_name
        })

    except Exception as e:
        print(f"[Chat] Error: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Chat error: {str(e)}'})


@socketio.on('synthesize')
def handle_synthesize(data):
    """Convert text to speech with streaming support (DashScope only)"""
    session_id = data.get('session_id')
    text = data.get('text')
    stream = data.get('stream', True)  # Default to streaming for better UX

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    session = sessions[session_id]

    # Get appropriate TTS service (always use DashScope for TTS)
    tts_service = dashscope_service if config.PROVIDER == 'dashscope' else dashscope_service

    if not tts_service:
        emit('error', {'message': 'DashScope service not available'})
        return

    try:
        # Get voice for this table
        voice = voices_data.get('tables', {}).get(session.table_id, 'Cherry')

        print(f"[TTS] Synthesizing text: {text[:50]}... (voice: {voice}, stream: {stream})")

        if stream:
            # Streaming mode - send audio chunks progressively
            print(f"[TTS] Starting streaming synthesis")

            # Notify client that streaming is starting
            emit('synthesis_started', {
                'session_id': session_id
            })

            # Stream audio chunks
            chunk_count = 0
            for audio_chunk in dashscope_service.synthesize(text, voice=voice, language_type='Auto', stream=True):
                chunk_count += 1

                # Send chunk to client
                emit('audio_chunk', {
                    'session_id': session_id,
                    'chunk_type': audio_chunk['type'],
                    'audio_data': audio_chunk['data'],
                    'chunk_number': chunk_count,
                    'is_final': False
                })

                print(f"[TTS] Sent chunk {chunk_count} ({audio_chunk['type']}) to client")

            # Send final marker
            emit('audio_chunk', {
                'session_id': session_id,
                'is_final': True
            })

            print(f"[TTS] Streaming complete: {chunk_count} chunks sent")

        else:
            # Non-streaming mode - send complete audio URL
            audio_url = dashscope_service.synthesize(text, voice=voice, language_type='Auto', stream=False)

            print(f"[TTS] Audio URL received: {audio_url}")

            if not audio_url:
                print(f"[TTS] Warning: audio_url is None or empty")
                emit('error', {'message': 'TTS returned no audio URL'})
                return

            emit('synthesis_complete', {
                'session_id': session_id,
                'audio_url': audio_url
            })

            print(f"[TTS] Synthesis complete, URL sent to client")

    except Exception as e:
        print(f"[TTS] Error: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'TTS error: {str(e)}'})


@app.route('/api/menu', methods=['GET'])
def get_menu():
    """Get full menu data"""
    return jsonify(menu_data)


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details"""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404

    session = sessions[session_id]

    return jsonify({
        'session_id': session.session_id,
        'table_name': session.table_name,
        'role': session.role,
        'party_size': session.party_size,
        'dietary_restrictions': session.dietary_restrictions,
        'current_order': session.current_order,
        'conversation_history': session.conversation_history[-20:]
    })


@socketio.on('reset_session')
def handle_reset_session(data):
    """Manual session reset (staff action or payment complete)"""
    session_id = data.get('session_id')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    try:
        # Clear session
        session = sessions[session_id]
        print(f"[Session] Manual reset for {session.table_name}")

        del sessions[session_id]

        emit('session_reset', {
            'session_id': session_id,
            'message': 'Session reset successfully'
        })

        print(f"[Session] Reset complete, ready for next customer")

    except Exception as e:
        print(f"[Session] Reset error: {e}")
        emit('error', {'message': f'Reset error: {str(e)}'})


@socketio.on('stop_listening')
def handle_stop_listening(data):
    """Stop passive listening mode"""
    session_id = data.get('session_id')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    try:
        session = sessions[session_id]

        if session.state == config.SessionState.CONFIRMED_PASSIVE:
            session.state = config.SessionState.CONFIRMED_STOPPED

            emit('state_changed', {
                'session_id': session_id,
                'state': 'confirmed_stopped',
                'show_stop_button': False
            })

            print(f"[Session] Passive listening stopped for {session.table_name}")

    except Exception as e:
        print(f"[Session] Stop listening error: {e}")
        emit('error', {'message': f'Stop listening error: {str(e)}'})


@socketio.on('resume_conversation')
def handle_resume_conversation(data):
    """Resume active conversation from passive/stopped state"""
    session_id = data.get('session_id')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    try:
        session = sessions[session_id]

        if session.state in [config.SessionState.CONFIRMED_PASSIVE, config.SessionState.CONFIRMED_STOPPED]:
            session.state = config.SessionState.CONFIRMED

            emit('state_changed', {
                'session_id': session_id,
                'state': 'confirmed',
                'show_stop_button': False
            })

            print(f"[Session] Resumed active conversation for {session.table_name}")
            print(f"[Session] Passive context: {len(session.passive_transcripts)} transcripts")

    except Exception as e:
        print(f"[Session] Resume conversation error: {e}")
        emit('error', {'message': f'Resume conversation error: {str(e)}'})


@socketio.on('start_ordering')
def handle_start_ordering(data):
    """Transition from ENROLLING to ORDERING state"""
    session_id = data.get('session_id')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    session = sessions[session_id]

    if session.state == config.SessionState.ENROLLING:
        session.state = config.SessionState.ORDERING
        print(f"[Session] State transition: ENROLLING → ORDERING")

        emit('state_changed', {
            'session_id': session_id,
            'state': 'ordering'
        })


if __name__ == '__main__':
    # Validate provider configuration
    try:
        config.validate_provider_config()
    except ValueError as e:
        print(f"[Error] Configuration error: {e}")
        exit(1)

    # Create directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)

    # Initialize ASR hot words for DashScope (improves recognition accuracy)
    if config.PROVIDER == 'dashscope':
        print("[Init] Setting up ASR hot words...")
        init_asr_phrases()

    print("="*60)
    print("CamareraI - Streaming Voice Agent POC")
    print("="*60)
    print(f"Provider: {config.PROVIDER}")
    if config.PROVIDER == 'gemini':
        print(f"Model: {config.GEMINI_LIVE_MODEL}")
    print(f"Server starting on http://{config.HOST}:{config.PORT}")
    print("Press Ctrl+C to stop")
    print("="*60)

    # Start the server
    socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG, allow_unsafe_werkzeug=True)
