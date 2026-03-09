"""
Streaming Voice Recognition Server using WebSocket and DashScope
Real-time ASR with streaming audio input
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from dashscope_client import DashScopeClient
import json
import os
from datetime import datetime
import uuid
import base64
from dashscope.audio.asr import Recognition
import dashscope
from http import HTTPStatus
from streaming_utils import has_sentence_ending
from performance_monitor import PerformanceMetrics
from openai import OpenAI
import config
from services.order_service import OrderService
from services.llm_service import LLMService

# Import ASR hot words support
from asr_vocabulary import get_or_create_phrases

# Set DashScope API key globally (required for Recognition class)
dashscope.api_key = config.DASHSCOPE_API_KEY

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
socketio = SocketIO(app, **config.SOCKETIO_CONFIG)

# Initialize ASR hot words phrase ID (cached)
# This improves recognition accuracy for restaurant-specific terms
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

# Initialize DashScope client
dashscope_client = DashScopeClient()

# Initialize OpenAI client for function calling (DashScope compatible)
# Using persistent HTTP session for connection reuse (performance optimization)
openai_client = OpenAI(
    api_key=config.DASHSCOPE_API_KEY,
    base_url=config.DASHSCOPE_BASE_URL,
    http_client=config.HTTP_CLIENT
)

# Initialize performance monitoring
perf_monitor = PerformanceMetrics(max_history=config.MAX_PERFORMANCE_HISTORY)

# Initialize LLM service
llm_service = LLMService(openai_client, dashscope_client, perf_monitor)


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

            # Warm up LLM connection with minimal request
            _ = openai_client.chat.completions.create(
                model='qwen-plus',
                messages=[{'role': 'user', 'content': 'hi'}],
                max_tokens=1,
                stream=False
            )

            print("[Perf] ✓ Connections pre-warmed")
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
            if rec_data['started']:
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
    """Start streaming ASR"""
    session_id = data.get('session_id')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    try:
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
            max_sentence_silence=5000,  # Increased from 2500ms to 5000ms to capture longer pauses
            disfluency_removal_enabled=False
        )

        # Store recognition instance with metadata (don't start yet)
        active_recognitions[request.sid] = {
            'recognition': recognition,
            'started': False,
            'session_id': session_id,
            'callback': callback
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
    """Stop streaming ASR"""
    try:
        if request.sid in active_recognitions:
            rec_data = active_recognitions[request.sid]
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
    """Process chat message with function calling (Option 4)"""
    session_id = data.get('session_id')
    message = data.get('message')

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
    """Convert text to speech with streaming support"""
    session_id = data.get('session_id')
    text = data.get('text')
    stream = data.get('stream', True)  # Default to streaming for better UX

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    session = sessions[session_id]

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
            for audio_chunk in dashscope_client.synthesize(text, voice=voice, language_type='Auto', stream=True):
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
            audio_url = dashscope_client.synthesize(text, voice=voice, language_type='Auto', stream=False)

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
    # Create directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)

    # Initialize ASR hot words (improves recognition accuracy)
    print("[Init] Setting up ASR hot words...")
    init_asr_phrases()

    print("="*60)
    print("CamareraI - Streaming Voice Agent POC")
    print("="*60)
    print(f"Server starting on http://{config.HOST}:{config.PORT}")
    print("Press Ctrl+C to stop")
    print("="*60)

    # Start the server
    socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG, allow_unsafe_werkzeug=True)
