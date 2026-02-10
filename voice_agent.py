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
from dotenv import load_dotenv
from dashscope.audio.asr import Recognition
import dashscope

load_dotenv()

# Set DashScope API key globally (required for Recognition class)
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    engineio_logger=False,
    logger=False,
    ping_timeout=60,
    ping_interval=25
)

# Initialize DashScope client
dashscope_client = DashScopeClient()

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


class SessionState:
    """Session state constants"""
    IDLE = 'idle'
    ENROLLING = 'enrolling'
    ORDERING = 'ordering'
    CONFIRMED = 'confirmed'
    CONFIRMED_PASSIVE = 'confirmed_passive'  # Passive listening (no AI response)
    CONFIRMED_STOPPED = 'confirmed_stopped'  # Listening stopped


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
        self.state = SessionState.IDLE

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
            if self.state == SessionState.CONFIRMED:
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

                        # Check if session is in passive mode
                        if self.session_id in sessions:
                            session = sessions[self.session_id]

                            if session.state == SessionState.CONFIRMED_PASSIVE:
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
    session.state = SessionState.ORDERING  # Start in ORDERING state to capture orders immediately
    sessions[session.session_id] = session

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
            recognition.start()
            rec_data['started'] = True
            print(f"[ASR] Recognition started for session {rec_data['session_id']}")

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
    """Process chat message and generate response"""
    session_id = data.get('session_id')
    message = data.get('message')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    session = sessions[session_id]

    try:
        # Add user message to history
        session.add_message('user', message)

        # Build messages for LLM with order extraction
        system_prompt = session.get_system_prompt()

        # Add order extraction instruction with menu context
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

        # State-aware order extraction prompt
        if session.state == SessionState.ORDERING:
            order_extraction_prompt = f"""
IMPORTANT: When customer orders items, extract them and format as JSON.

Available menu items:
{chr(10).join([f"- {item['en']} / {item['zh']} / {item['yue']}: ${item['price']}" for item in menu_items_list[:15]])}

When customer mentions ordering items, add this at the END of your response:

ORDER_UPDATE: {{"action": "add", "items": [{{"name": "Item Name", "quantity": 1, "price": 14.99, "modifications": []}}]}}

Actions:
- "add": Customer orders new items
- "remove": Customer cancels items (e.g., "cancel the soup", "remove the chicken")
- "modify": Customer changes quantity (e.g., "make that two", "change to three")

Examples:
Customer: "I'll have the Kung Pao Chicken"
Response: Great choice! One Kung Pao Chicken coming up.

ORDER_UPDATE: {{"action": "add", "items": [{{"name": "Kung Pao Chicken", "quantity": 1, "price": 14.99, "modifications": []}}]}}

Customer: "我要宫保鸡丁"
Response: 好的！一份宫保鸡丁。

ORDER_UPDATE: {{"action": "add", "items": [{{"name": "宫保鸡丁", "quantity": 1, "price": 14.99, "modifications": []}}]}}

Customer: "Actually, make that two"
Response: No problem! I'll change that to two orders.

ORDER_UPDATE: {{"action": "modify", "items": [{{"name": "Kung Pao Chicken", "quantity": 2, "price": 14.99, "modifications": []}}]}}

Customer: "Cancel the soup"
Response: Sure, I'll remove the soup from your order.

ORDER_UPDATE: {{"action": "remove", "items": [{{"name": "Spring Rolls", "quantity": 1, "price": 8.99, "modifications": []}}]}}

ONLY include ORDER_UPDATE when customer is actually ordering/modifying/removing items.
DO NOT include ORDER_UPDATE for questions, recommendations, or general conversation.
"""
        elif session.state == SessionState.CONFIRMED:
            # Build confirmed order summary
            confirmed_summary = "No confirmed items"
            if session.confirmed_items:
                confirmed_items_list = []
                for item in session.confirmed_items:
                    confirmed_items_list.append(f"- {item['name']} x{item['quantity']} (${item['price']})")
                confirmed_summary = '\n'.join(confirmed_items_list)

            order_extraction_prompt = f"""
IMPORTANT: The order has been CONFIRMED. Customer can ONLY add MORE items.

Confirmed Order (LOCKED - cannot be modified or removed):
{confirmed_summary}

Available menu items:
{chr(10).join([f"- {item['en']} / {item['zh']} / {item['yue']}: ${item['price']}" for item in menu_items_list[:15]])}

Customer can:
- Add MORE items (new orders)
- Ask questions
- Request service

Customer CANNOT modify or remove confirmed items.

If customer tries to modify/remove confirmed items, politely explain:
- English: "Your order has been confirmed. I can add more items, but cannot modify the confirmed order. Would you like to add something else?"
- Mandarin: "您的订单已确认。我可以添加更多菜品，但无法修改已确认的订单。您想添加其他菜品吗？"
- Cantonese: "你嘅訂單已經確認咗。我可以加多啲嘢，但係唔可以改已經確認嘅訂單。你想加其他嘢嗎？"

When customer orders NEW items, add this at the END of your response:

ORDER_UPDATE: {{"action": "add", "items": [{{"name": "Item Name", "quantity": 1, "price": 14.99, "modifications": []}}]}}

ONLY use action "add". DO NOT use "modify" or "remove" actions.
"""
        else:
            # Default prompt for other states
            order_extraction_prompt = ""

        messages = [
            {'role': 'system', 'content': system_prompt + '\n\n' + order_extraction_prompt}
        ]

        # Add recent conversation history
        for msg in session.conversation_history[-10:]:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })

        # Get AI response
        response = dashscope_client.chat(messages, model='qwen-turbo')

        # Parse order updates from response
        order_update = None
        clean_response = response

        if 'ORDER_UPDATE:' in response:
            parts = response.split('ORDER_UPDATE:')
            clean_response = parts[0].strip()
            try:
                import json
                # Extract only the JSON object, ignoring any extra text after
                order_text = parts[1].strip()

                # Find the JSON object boundaries
                start_idx = order_text.find('{')
                if start_idx == -1:
                    raise ValueError("No JSON object found after ORDER_UPDATE:")

                # Find matching closing brace
                brace_count = 0
                end_idx = -1
                for i in range(start_idx, len(order_text)):
                    if order_text[i] == '{':
                        brace_count += 1
                    elif order_text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break

                if end_idx == -1:
                    raise ValueError("No matching closing brace found in ORDER_UPDATE JSON")

                order_json = order_text[start_idx:end_idx]
                print(f"[Order] Extracted JSON: {order_json}")
                order_update = json.loads(order_json)

                # Process order update based on session state
                if session.state == SessionState.CONFIRMED:
                    # In CONFIRMED state, only allow "add" actions
                    if order_update['action'] in ['modify', 'remove']:
                        print(f"[Order] Rejected {order_update['action']} in CONFIRMED state")
                        # Don't process the order update, LLM should have refused
                        # But if it slipped through, ignore it
                    elif order_update['action'] == 'add':
                        for item in order_update['items']:
                            session.current_order.append(item)
                            print(f"[Order] Added (CONFIRMED state): {item['name']} x{item['quantity']} - ${item['price']}")

                elif session.state == SessionState.ORDERING:
                    # In ORDERING state, allow all actions
                    if order_update['action'] == 'add':
                        for item in order_update['items']:
                            session.current_order.append(item)
                            print(f"[Order] Added: {item['name']} x{item['quantity']} - ${item['price']}")

                    elif order_update['action'] == 'remove':
                        for item in order_update['items']:
                            # Remove matching items (match by name in any language)
                            item_name = item['name'].lower()
                            session.current_order = [
                                o for o in session.current_order
                                if o['name'].lower() != item_name
                            ]
                            print(f"[Order] Removed: {item['name']}")

                    elif order_update['action'] == 'modify':
                        for item in order_update['items']:
                            # Find and update item quantity
                            item_name = item['name'].lower()
                            found = False
                            for o in session.current_order:
                                if o['name'].lower() == item_name:
                                    o['quantity'] = item['quantity']
                                    found = True
                                    print(f"[Order] Modified: {item['name']} -> x{item['quantity']}")
                                    break

                            # If not found, treat as add
                            if not found:
                                session.current_order.append(item)
                                print(f"[Order] Added (via modify): {item['name']} x{item['quantity']}")

                # Calculate order totals (include both confirmed and current items)
                all_items = session.confirmed_items + session.current_order
                subtotal = sum(item['price'] * item['quantity'] for item in all_items)
                tax = subtotal * 0.09
                total = subtotal + tax

                # Send order update to client
                emit('order_updated', {
                    'session_id': session_id,
                    'confirmed_items': session.confirmed_items,
                    'current_order': session.current_order,
                    'action': order_update['action'],
                    'subtotal': round(subtotal, 2),
                    'tax': round(tax, 2),
                    'total': round(total, 2)
                })

                print(f"[Order] Total items: {len(all_items)}, Total: ${total:.2f}")

            except Exception as e:
                print(f"[Order] Failed to parse order update: {e}")
                import traceback
                traceback.print_exc()

        # If clean_response is empty (ORDER_UPDATE at beginning), use a default acknowledgment
        if not clean_response or not clean_response.strip():
            # Determine language from last user message
            last_user_msg = next((msg['content'] for msg in reversed(session.conversation_history) if msg['role'] == 'user'), '')

            # Simple language detection based on character ranges
            if any('\u4e00' <= c <= '\u9fff' for c in last_user_msg):
                # Chinese characters detected
                if any(c in '係咩嘅啲' for c in last_user_msg):
                    clean_response = "好嘅！"  # Cantonese
                else:
                    clean_response = "好的！"  # Mandarin
            else:
                clean_response = "Got it!"  # English

            print(f"[Order] Empty response, using default: {clean_response}")

        # Check for closing remark and handle state transition
        if session._is_closing_remark(message):
            if session.state == SessionState.ORDERING:
                # First confirmation - lock order and enter passive mode
                session.confirmed_items.extend(session.current_order)
                session.current_order = []
                session.state = SessionState.CONFIRMED_PASSIVE
                session.order_confirmed_at = datetime.now()

                print(f"[Session] State transition: ORDERING → CONFIRMED_PASSIVE")
                print(f"[Session] Locked {len(session.confirmed_items)} items")

                # Calculate totals
                subtotal = sum(item['price'] * item['quantity'] for item in session.confirmed_items)
                tax = subtotal * 0.09
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

            elif session.state == SessionState.CONFIRMED:
                # Additional confirmation - lock new items and return to passive
                if session.current_order:
                    session.confirmed_items.extend(session.current_order)
                    session.current_order = []
                    session.state = SessionState.CONFIRMED_PASSIVE

                    print(f"[Session] Additional confirmation: CONFIRMED → CONFIRMED_PASSIVE")
                    print(f"[Session] Total locked items: {len(session.confirmed_items)}")

                    # Calculate totals
                    subtotal = sum(item['price'] * item['quantity'] for item in session.confirmed_items)
                    tax = subtotal * 0.09
                    total = subtotal + tax

                    # Notify client of order update
                    emit('order_updated', {
                        'session_id': session_id,
                        'confirmed_items': session.confirmed_items,
                        'current_order': [],
                        'action': 'confirm',
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

        # Add AI response to history
        session.add_message('assistant', clean_response)

        emit('chat_response', {
            'session_id': session_id,
            'response': clean_response,
            'table_name': session.table_name
        })

    except Exception as e:
        print(f"[Chat] Error: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Chat error: {str(e)}'})


@socketio.on('synthesize')
def handle_synthesize(data):
    """Convert text to speech"""
    session_id = data.get('session_id')
    text = data.get('text')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    session = sessions[session_id]

    try:
        # Get voice for this table
        voice = voices_data.get('tables', {}).get(session.table_id, 'Cherry')

        print(f"[TTS] Synthesizing text: {text[:50]}... (voice: {voice})")

        # Synthesize speech
        audio_url = dashscope_client.synthesize(text, voice=voice, language_type='Auto')

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

        if session.state == SessionState.CONFIRMED_PASSIVE:
            session.state = SessionState.CONFIRMED_STOPPED

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

        if session.state in [SessionState.CONFIRMED_PASSIVE, SessionState.CONFIRMED_STOPPED]:
            session.state = SessionState.CONFIRMED

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

    if session.state == SessionState.ENROLLING:
        session.state = SessionState.ORDERING
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

    print("="*60)
    print("CamareraI - Streaming Voice Agent POC")
    print("="*60)
    print(f"Server starting on http://0.0.0.0:5002")
    print("Press Ctrl+C to stop")
    print("="*60)

    # Start the server
    socketio.run(app, host='0.0.0.0', port=5002, debug=True, allow_unsafe_werkzeug=True)
