"""
Voice Agent - DashScope Provider Implementation
Complete streaming implementation using DashScope for ASR, LLM, and TTS
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import uuid
import base64
import threading
import queue

import config
from models.conversation_session import ConversationSession
from routes.api import load_json_data, register_routes
from services.order_service import OrderService
from services.dashscope_service import DashScopeService
from services.llm_service import LLMService
from performance_monitor import PerformanceMetrics

from openai import OpenAI
from dashscope.audio.asr import Recognition
import dashscope
from asr_vocabulary import get_or_create_phrases


# ============================================================================
# Initialize DashScope
# ============================================================================

dashscope.api_key = config.DASHSCOPE_API_KEY

# Initialize services
dashscope_service = DashScopeService()
openai_client = OpenAI(
    api_key=config.DASHSCOPE_API_KEY,
    base_url=config.DASHSCOPE_BASE_URL,
    http_client=config.HTTP_CLIENT
)
llm_service = LLMService(openai_client, dashscope_service, None)  # perf_monitor set later
order_service = OrderService()

# Initialize performance monitoring
perf_monitor = PerformanceMetrics(max_history=config.MAX_PERFORMANCE_HISTORY)
llm_service.perf_monitor = perf_monitor

# Get or create ASR hot word phrases
asr_phrase_id = get_or_create_phrases()

# ============================================================================
# Flask & SocketIO Setup
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

socketio = SocketIO(app, **config.SOCKETIO_CONFIG)

# ============================================================================
# Data Loading
# ============================================================================

menu_data = load_json_data('menu.json')
knowledge_data = load_json_data('knowledge.json')
table_names = load_json_data('table_names.json')
voices_data = load_json_data('voices.json')

# ============================================================================
# Session Management
# ============================================================================

sessions = {}  # session_id -> ConversationSession
recognition_instances = {}  # session_id -> Recognition instance


def get_or_create_session(table_id, role='customer'):
    """Get existing session or create new one for a table"""
    # Check for existing session for this table
    for session in sessions.values():
        if session.table_id == table_id and session.state != config.SessionState.CONFIRMED_STOPPED:
            return session

    # Create new session
    session = ConversationSession(table_id, role, table_names)
    sessions[session.session_id] = session
    return session


def cleanup_session(session_id):
    """Clean up a session"""
    if session_id in sessions:
        del sessions[session_id]
    if session_id in recognition_instances:
        del recognition_instances[session_id]


# ============================================================================
# ASR Recognition Callback Factory
# ============================================================================

def create_recognition_callback(session_id):
    """Create callback functions for ASR recognition"""

    def on_start(recognition):
        print(f"[ASR] Recognition started for session {session_id}")
        socketio.emit('recognition_started', {'session_id': session_id})

    def on_complete(recognition):
        print(f"[ASR] Recognition completed for session {session_id}")
        perf_monitor.end_timer('asr')
        perf_monitor.mark_event('asr_complete')

    def on_error(recognition, error):
        print(f"[ASR] Recognition error for session {session_id}: {error}")
        socketio.emit('recognition_error', {
            'session_id': session_id,
            'error': str(error)
        })

    def on_event(recognition, result):
        """Handle ASR result events"""
        if result.is_sentence_end:
            transcript = result.text if hasattr(result, 'text') else str(result)
            print(f"[ASR] Transcript: {transcript}")

            # Store transcript in session
            if session_id in sessions:
                sessions[session_id].add_message('user', transcript)

            # Emit to client
            socketio.emit('transcript', {
                'session_id': session_id,
                'text': transcript,
                'is_final': True
            })

            # Process with LLM
            process_chat(session_id, transcript)

    return on_start, on_complete, on_error, on_event


# ============================================================================
# LLM Chat Processing
# ============================================================================

def process_chat(session_id, transcript):
    """Process chat message with LLM and stream response"""
    if session_id not in sessions:
        print(f"[Chat] Session {session_id} not found")
        return

    session = sessions[session_id]

    # Build system prompt
    system_prompt = build_system_prompt(session)

    # Prepare messages
    messages = [
        {'role': 'system', 'content': system_prompt},
        *session.get_messages_for_llm(limit=10),
        {'role': 'user', 'content': transcript}
    ]

    # Get voice from session or default
    voice = voices_data.get('default_voice', 'Cherry')

    # Start performance tracking
    perf_monitor.start_timer('llm')

    # Stream LLM response with function calling
    content_buffer, tool_call_buffer = llm_service.stream_with_function_calling(
        messages=messages,
        tools=[config.ORDER_UPDATE_TOOL],
        voice=voice,
        session_id=session_id,
        emit_func=socketio.emit
    )

    # Process any tool calls
    if tool_call_buffer.get('name') == 'update_order':
        result = order_service.process_tool_call(
            tool_call_buffer,
            session=session,
            menu_data=menu_data
        )

        # Emit order update
        socketio.emit('order_update', {
            'session_id': session_id,
            'order': result.get('order', {}),
            'action': result.get('action', 'unknown')
        })

    # Add assistant response to conversation
    if content_buffer:
        session.add_message('assistant', content_buffer)

    # Record performance
    perf_monitor.end_timer('llm')
    perf_monitor.record_request()


def build_system_prompt(session):
    """Build system prompt for LLM"""
    menu_context = format_menu_for_prompt(menu_data)
    knowledge_context = format_knowledge_for_prompt(knowledge_data)

    prompt = f"""You are 'Lily', a helpful interactive waiter at a Chinese restaurant.
Your goal is to help customers order food, explain the menu, and share cultural context.
You must reply in the SAME language the user speaks (English, Mandarin, or Cantonese).

Current table: {session.table_name}
Party size: {session.party_size or 'Unknown'}

{menu_context}

{knowledge_context}

You can use the update_order function to add, modify, or remove items from the customer's order.
Always confirm the order details with the customer before finalizing.
Keep responses concise (1-2 sentences conversational).
"""
    return prompt


def format_menu_for_prompt(menu_data):
    """Format menu data for LLM prompt"""
    if not menu_data or 'menu' not in menu_data:
        return ""

    lines = ["Available Menu Items:"]
    for category, items in menu_data['menu'].items():
        lines.append(f"\n{category}:")
        for item in items[:10]:  # Limit to 10 items per category
            name = item.get('name', {})
            if isinstance(name, dict):
                name_str = f"{name.get('en', '')} ({name.get('zh', '')})"
            else:
                name_str = name
            price = item.get('price', 0)
            desc = item.get('description', {}).get('en', '')
            lines.append(f"  - {name_str}: ${price}")
            if desc:
                lines.append(f"    {desc}")
    return "\n".join(lines)


def format_knowledge_for_prompt(knowledge_data):
    """Format knowledge base for LLM prompt"""
    if not knowledge_data:
        return ""

    lines = ["\nRestaurant Knowledge:"]
    for topic, info in knowledge_data.items():
        if isinstance(info, dict):
            content = info.get('content', '')
            if content:
                lines.append(f"- {topic}: {content}")
        elif isinstance(info, str):
            lines.append(f"- {topic}: {info}")
    return "\n".join(lines)


# ============================================================================
# HTTP Routes
# ============================================================================

register_routes(app, sessions, menu_data, knowledge_data, voices_data, table_names)


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


# ============================================================================
# SocketIO Event Handlers
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"[Socket] Client connected: {request.sid if hasattr(request, 'sid') else 'unknown'}")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"[Socket] Client disconnected")


@socketio.on('start_session')
def handle_start_session(data):
    """Start a new session for a table"""
    table_id = data.get('table_id', '1')
    role = data.get('role', 'customer')

    session = get_or_create_session(table_id, role)

    emit('session_started', {
        'session_id': session.session_id,
        'table_name': session.table_name,
        'state': session.state
    })

    print(f"[Session] Started session {session.session_id} for table {table_id}")


@socketio.on('start_recognition')
def handle_start_recognition(data):
    """Start ASR recognition for a session"""
    session_id = data.get('session_id')
    if session_id not in sessions:
        emit('error', {'message': 'Session not found'})
        return

    # Create recognition instance
    on_start, on_complete, on_error, on_event = create_recognition_callback(session_id)

    recognition = Recognition(
        model='paraformer-realtime-v2',
        format='pcm',
        sample_rate=16000,
        callback=[
            on_start,
            on_complete,
            on_error,
            on_event
        ]
    )

    # Start recognition
    recognition.start(
        phrase_id=asr_phrase_id,
        # Only set disfluency_removal for Chinese ASR
        disfluency_removal=True if config.ASR_PROVIDER == 'dashscope' else None
    )

    recognition_instances[session_id] = recognition

    # Start performance tracking
    perf_monitor.start_timer('asr')

    emit('recognition_started', {'session_id': session_id})
    print(f"[ASR] Started recognition for session {session_id}")


@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle audio data from client"""
    session_id = data.get('session_id')
    audio_base64 = data.get('audio')

    if not session_id or not audio_base64:
        return

    if session_id not in recognition_instances:
        return

    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)

        # Send to recognition
        recognition_instances[session_id].send_audio(audio_bytes)
    except Exception as e:
        print(f"[Audio] Error processing audio: {e}")


@socketio.on('stop_recognition')
def handle_stop_recognition(data):
    """Stop ASR recognition"""
    session_id = data.get('session_id')

    if session_id in recognition_instances:
        recognition_instances[session_id].stop()
        del recognition_instances[session_id]

    emit('recognition_stopped', {'session_id': session_id})
    print(f"[ASR] Stopped recognition for session {session_id}")


@socketio.on('chat')
def handle_chat(data):
    """Handle chat message (text-based)"""
    session_id = data.get('session_id')
    message = data.get('message', '')

    if not session_id or not message:
        emit('error', {'message': 'Missing session_id or message'})
        return

    if session_id not in sessions:
        emit('error', {'message': 'Session not found'})
        return

    # Add to session
    sessions[session_id].add_message('user', message)

    # Process with LLM
    process_chat(session_id, message)


@socketio.on('tts')
def handle_tts(data):
    """Handle TTS request"""
    session_id = data.get('session_id')
    text = data.get('text', '')
    voice = data.get('voice', voices_data.get('default_voice', 'Cherry'))

    if not session_id or not text:
        emit('error', {'message': 'Missing session_id or text'})
        return

    emit('synthesis_started', {'session_id': session_id})

    try:
        chunk_count = 0
        for audio_chunk in dashscope_service.synthesize(
            text[:config.MAX_TTS_LENGTH],
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

        print(f"[TTS] Completed: {chunk_count} chunks")

    except Exception as e:
        print(f"[TTS] Error: {e}")
        emit('error', {'message': f'TTS error: {str(e)}'})


@socketio.on('confirm_order')
def handle_confirm_order(data):
    """Confirm the current order"""
    session_id = data.get('session_id')

    if session_id not in sessions:
        emit('error', {'message': 'Session not found'})
        return

    session = sessions[session_id]
    session.confirm_order()

    emit('order_confirmed', {
        'session_id': session_id,
        'confirmed_items': session.confirmed_items
    })

    print(f"[Order] Confirmed for session {session_id}")


@socketio.on('update_state')
def handle_update_state(data):
    """Update session state"""
    session_id = data.get('session_id')
    new_state = data.get('state')

    if session_id not in sessions:
        emit('error', {'message': 'Session not found'})
        return

    if new_state in [config.SessionState.IDLE, config.SessionState.ORDERING,
                     config.SessionState.CONFIRMED, config.SessionState.CONFIRMED_PASSIVE,
                     config.SessionState.CONFIRMED_STOPPED]:
        sessions[session_id].state = new_state
        emit('state_updated', {'session_id': session_id, 'state': new_state})


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    print(f"[Server] Starting DashScope Voice Agent on {config.HOST}:{config.PORT}")
    print(f"[Provider] ASR: {config.ASR_PROVIDER}, LLM: {config.LLM_PROVIDER}, TTS: {config.TTS_PROVIDER}")
    socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG)
