"""
Streaming Voice Recognition Server using WebSocket and DashScope
Real-time ASR with streaming audio input
OPTION 4: Function calling for clean order updates
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
from http import HTTPStatus
from streaming_utils import has_sentence_ending
from performance_monitor import PerformanceMetrics
from openai import OpenAI

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

# Initialize OpenAI client for function calling (DashScope compatible)
openai_client = OpenAI(
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
)

# Initialize performance monitoring
perf_monitor = PerformanceMetrics(max_history=100)

# Define order update tool for function calling
ORDER_UPDATE_TOOL = {
    "type": "function",
    "function": {
        "name": "update_order",
        "description": "Update the customer's food order with add, modify, or remove actions",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "modify", "remove"],
                    "description": "The action to perform on the order"
                },
                "items": {
                    "type": "array",
                    "description": "List of items to add, modify, or remove",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the dish"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "Quantity of the dish"
                            },
                            "price": {
                                "type": "number",
                                "description": "Price per item"
                            },
                            "modifications": {
                                "type": "array",
                                "description": "Special modifications or requests",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["name", "quantity", "price"]
                    }
                }
            },
            "required": ["action", "items"]
        }
    }
}

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
    CONFIRMED_PASSIVE = 'confirmed_passive'
    CONFIRMED_STOPPED = 'confirmed_stopped'


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
        self.current_order = []
        self.confirmed_items = []
        self.order_confirmed_at = None

        # Passive listening
        self.passive_transcripts = []

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

        english_closings = [
            'thank you', 'thanks', "that's all", 'go ahead',
            'send the order', "that'll be all", 'thats all',
            "that's it", 'thats it'
        ]

        mandarin_closings = [
            '谢谢', '好的', '可以了', '就这些', '下单吧',
            '没了', '够了', '行了'
        ]

        cantonese_closings = [
            '唔該', '多謝', '得啦', '可以啦', '落單啦',
            '夠啦', '冇啦'
        ]

        for closing in english_closings + mandarin_closings + cantonese_closings:
            if closing in message_lower:
                return True

        return False

    def get_system_prompt(self):
        """Generate role-specific system prompt"""
        restaurant_name = menu_data.get('restaurant', {}).get('name', 'Golden Dragon')

        if self.role == 'customer':
            order_summary = "No items yet"
            if self.current_order:
                order_items = []
                for item in self.current_order:
                    order_items.append(f"- {item['name']} x{item['quantity']} (${item['price']})")
                order_summary = '\n'.join(order_items)

            passive_context = ""
            if self.passive_transcripts:
                passive_context = f"""

Context from customer conversation (captured while dining):
{chr(10).join(f"- {t}" for t in self.passive_transcripts[-5:])}

Use this context to better understand customer preferences and needs.
"""

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


# Import the rest of the handlers from original voice_agent.py
# (StreamingRecognitionCallback, routes, etc.)
# For brevity, I'll focus on the key change: handle_chat_with_function_calling

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
        if session.state == SessionState.ORDERING:
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
        elif session.state == SessionState.CONFIRMED:
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

        # Start performance tracking
        perf_monitor.start_timer('llm')
        perf_monitor.mark_event('llm_start')

        print(f"[LLM] Starting streaming with function calling")

        # Get voice for this table
        voice = voices_data.get('tables', {}).get(session.table_id, 'Cherry')

        # Stream with function calling
        stream = openai_client.chat.completions.create(
            model='qwen-plus',
            messages=messages,
            tools=[ORDER_UPDATE_TOOL],
            tool_choice='auto',
            stream=True
        )

        # Track streaming data
        content_buffer = ""
        sentence_buffer = ""
        tool_call_buffer = {"id": None, "name": None, "arguments": ""}

        # Notify client
        emit('llm_started', {'session_id': session_id})

        for chunk in stream:
            delta = chunk.choices[0].delta

            # Handle conversational text (stream to TTS)
            if delta.content:
                # Mark first LLM token
                if not content_buffer:
                    perf_monitor.mark_event('llm_first_chunk')
                    llm_first_token = perf_monitor.calculate_duration('llm_start', 'llm_first_chunk')
                    if llm_first_token:
                        print(f"[Perf] LLM first token in {llm_first_token:.0f}ms")

                content_buffer += delta.content
                sentence_buffer += delta.content

                # Send to client for display
                emit('llm_chunk', {
                    'session_id': session_id,
                    'text': delta.content
                })

                # Check for sentence ending
                if has_sentence_ending(sentence_buffer):
                    sentence_to_synthesize = sentence_buffer.strip()[:500]

                    print(f"[LLM→TTS] Streaming sentence: {sentence_to_synthesize[:50]}...")

                    # Mark TTS start
                    perf_monitor.mark_event('tts_start')

                    # Notify TTS starting
                    emit('synthesis_started', {'session_id': session_id})

                    # Stream to TTS
                    try:
                        first_audio_chunk = True
                        chunk_count = 0
                        for audio_chunk in dashscope_client.synthesize(
                            sentence_to_synthesize,
                            voice=voice,
                            language_type='Auto',
                            stream=True
                        ):
                            if first_audio_chunk:
                                perf_monitor.mark_event('first_audio')
                                first_audio_time = perf_monitor.calculate_duration('tts_start', 'first_audio')
                                if first_audio_time:
                                    print(f"[Perf] First audio in {first_audio_time:.0f}ms")
                                first_audio_chunk = False

                            chunk_count += 1
                            emit('audio_chunk', {
                                'session_id': session_id,
                                'chunk_type': audio_chunk['type'],
                                'audio_data': audio_chunk['data'],
                                'chunk_number': chunk_count,
                                'is_final': False
                            })

                        # Send final marker
                        emit('audio_chunk', {
                            'session_id': session_id,
                            'is_final': True
                        })
                        print(f"[TTS] Sentence streaming complete: {chunk_count} chunks sent")

                    except Exception as e:
                        print(f"[TTS] Streaming error: {e}")

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
            final_sentence = sentence_buffer.strip()[:500]
            print(f"[LLM→TTS] Final sentence: {final_sentence[:50]}...")

            emit('synthesis_started', {'session_id': session_id})

            try:
                chunk_count = 0
                for audio_chunk in dashscope_client.synthesize(
                    final_sentence,
                    voice=voice,
                    language_type='Auto',
                    stream=True
                ):
                    chunk_count += 1
                    emit('audio_chunk', {
                        'session_id': session_id,
                        'chunk_type': audio_chunk['type'],
                        'audio_data': audio_chunk['data'],
                        'chunk_number': chunk_count,
                        'is_final': False
                    })

                emit('audio_chunk', {
                    'session_id': session_id,
                    'is_final': True
                })
                print(f"[TTS] Final sentence streaming complete: {chunk_count} chunks sent")

            except Exception as e:
                print(f"[TTS] Streaming error: {e}")

        # Process tool call if present
        if tool_call_buffer["name"]:
            print(f"[Function Call] {tool_call_buffer['name']}")

            try:
                arguments = json.loads(tool_call_buffer["arguments"])

                if tool_call_buffer["name"] == "update_order":
                    action = arguments.get("action")
                    items = arguments.get("items", [])

                    print(f"[Order] Action: {action}, Items: {len(items)}")

                    # Process order update based on session state
                    if session.state == SessionState.CONFIRMED:
                        # Only allow "add" in CONFIRMED state
                        if action in ['modify', 'remove']:
                            print(f"[Order] Rejected {action} in CONFIRMED state")
                        elif action == 'add':
                            for item in items:
                                session.current_order.append(item)
                                print(f"[Order] Added (CONFIRMED state): {item['name']} x{item['quantity']} - ${item['price']}")

                    elif session.state == SessionState.ORDERING:
                        # Allow all actions in ORDERING state
                        if action == 'add':
                            for item in items:
                                session.current_order.append(item)
                                print(f"[Order] Added: {item['name']} x{item['quantity']} - ${item['price']}")

                        elif action == 'remove':
                            for item in items:
                                item_name = item['name'].lower()
                                session.current_order = [
                                    o for o in session.current_order
                                    if o['name'].lower() != item_name
                                ]
                                print(f"[Order] Removed: {item['name']}")

                        elif action == 'modify':
                            for item in items:
                                item_name = item['name'].lower()
                                found = False
                                for o in session.current_order:
                                    if o['name'].lower() == item_name:
                                        o['quantity'] = item['quantity']
                                        found = True
                                        print(f"[Order] Modified: {item['name']} -> x{item['quantity']}")
                                        break

                                if not found:
                                    session.current_order.append(item)
                                    print(f"[Order] Added (via modify): {item['name']} x{item['quantity']}")

                    # Calculate totals
                    all_items = session.confirmed_items + session.current_order
                    subtotal = sum(item['price'] * item['quantity'] for item in all_items)
                    tax = subtotal * 0.09
                    total = subtotal + tax

                    # Send order update to client
                    emit('order_updated', {
                        'session_id': session_id,
                        'confirmed_items': session.confirmed_items,
                        'current_order': session.current_order,
                        'action': action,
                        'subtotal': round(subtotal, 2),
                        'tax': round(tax, 2),
                        'total': round(total, 2)
                    })

                    print(f"[Order] Total items: {len(all_items)}, Total: ${total:.2f}")

            except Exception as e:
                print(f"[Order] Error processing tool call: {e}")
                import traceback
                traceback.print_exc()

        # Check for closing remark
        if session._is_closing_remark(message):
            if session.state == SessionState.ORDERING:
                session.confirmed_items.extend(session.current_order)
                session.current_order = []
                session.state = SessionState.CONFIRMED_PASSIVE
                session.order_confirmed_at = datetime.now()

                print(f"[Session] State transition: ORDERING → CONFIRMED_PASSIVE")
                print(f"[Session] Locked {len(session.confirmed_items)} items")

                subtotal = sum(item['price'] * item['quantity'] for item in session.confirmed_items)
                tax = subtotal * 0.09
                total = subtotal + tax

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


# Note: This is a simplified version showing the key changes for Option 4
# The full implementation would include all other handlers from voice_agent.py
# (create_session, start_recognition, stop_recognition, etc.)

if __name__ == '__main__':
    print("=" * 60)
    print("CamareraI - Streaming Voice Agent POC (Option 4)")
    print("=" * 60)
    print(f"Server starting on http://0.0.0.0:5002")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    socketio.run(app, host='0.0.0.0', port=5002, debug=True, allow_unsafe_werkzeug=True)
