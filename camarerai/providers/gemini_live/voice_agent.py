"""
Voice Agent - Gemini Live API Implementation
Uses Gemini Live API for bidirectional audio streaming (voice-in, voice-out)
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
import asyncio
import base64
import threading
import queue

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from camarerai import config
from camarerai.common.models.conversation_session import ConversationSession
from camarerai.common.routes.api import load_json_data, register_routes
from camarerai.common.services.order_service import OrderService
from camarerai.providers.gemini_live.services.gemini_live_service import GeminiLiveService
from camarerai.common.utils.performance_monitor import PerformanceMetrics


# ============================================================================
# Initialize Services
# ============================================================================

perf_monitor = PerformanceMetrics(max_history=config.MAX_PERFORMANCE_HISTORY)
order_service = OrderService()
gemini_service = GeminiLiveService(perf_monitor)

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


def get_or_create_session(table_id, role='customer'):
    """Get existing session or create new one for a table"""
    for session in sessions.values():
        if session.table_id == table_id and session.state != config.SessionState.CONFIRMED_STOPPED:
            return session

    session = ConversationSession(table_id, role, table_names)
    sessions[session.session_id] = session
    return session


def cleanup_session(session_id):
    """Clean up a session"""
    if session_id in sessions:
        del sessions[session_id]


# ============================================================================
# Async Helpers for Gemini Live
# ============================================================================

def run_async(coro):
    """Run an async coroutine in a new event loop thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def start_async_thread(coro):
    """Start a coroutine in a background thread"""
    thread = threading.Thread(target=lambda: run_async(coro))
    thread.daemon = True
    thread.start()
    return thread


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
    print(f"[Socket] Client connected")


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
    """Start Gemini Live API session"""
    session_id = data.get('session_id')

    if session_id not in sessions:
        emit('error', {'message': 'Session not found'})
        return

    session = sessions[session_id]

    # Build tools for order management
    tools = [config.ORDER_UPDATE_TOOL]

    # Set session data for order processing
    gemini_service.set_session_data(session, menu_data)

    # Start in background thread - emit recognition_started after connection
    # Use socketio.emit (not bare emit) for thread-safe emission without request context
    async def connect_and_run():
        try:
            await gemini_service.connect(
                session_id=session_id,
                emit_func=socketio.emit,
                order_service=order_service,
                tools=tools
            )
            # Emit only after successful connection
            socketio.emit('recognition_started', {'session_id': session_id})
            print(f"[Gemini Live] Connected for session {session_id}")
            # Run the session
            await gemini_service.run_session()
        except Exception as e:
            print(f"[Gemini Live] Error: {e}")
            socketio.emit('error', {'message': str(e)})

    thread = start_async_thread(connect_and_run())


@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle audio data from client - send to Gemini Live"""
    session_id = data.get('session_id')
    audio_base64 = data.get('audio')

    if not session_id or not audio_base64:
        return

    if not gemini_service.is_active():
        print(f"[Audio] Service not active, dropping {len(audio_base64) if audio_base64 else 0} bytes")
        return

    try:
        # Decode base64 audio and send to Gemini
        audio_bytes = base64.b64decode(audio_base64)
        print(f"[Audio] Received {len(audio_bytes)} bytes, sending to Gemini")

        # Use thread-safe method to send audio
        gemini_service.send_audio_sync(audio_bytes)
        print(f"[Audio] Sent to queue")

    except Exception as e:
        print(f"[Audio] Error sending to Gemini: {e}")
        import traceback
        traceback.print_exc()


@socketio.on('stop_recognition')
def handle_stop_recognition(data):
    """Stop Gemini Live API session"""
    session_id = data.get('session_id')

    async def disconnect():
        await gemini_service.disconnect()

    # Run disconnect in background
    start_async_thread(disconnect())

    emit('recognition_stopped', {'session_id': session_id})
    print(f"[Gemini Live] Disconnected for session {session_id}")


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

    session = sessions[session_id]
    session.add_message('user', message)

    # For Gemini Live, we need to send text as audio input
    # This would require a different approach or using the standard API
    emit('error', {'message': 'Text chat not supported in Gemini Live mode. Use voice.'})


@socketio.on('tts')
def handle_tts(data):
    """TTS is handled by Gemini Live API - no separate TTS needed"""
    emit('error', {'message': 'TTS is handled by Gemini Live API'})


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
    print(f"[Server] Starting Gemini Live Voice Agent on {config.HOST}:{config.PORT}")
    print(f"[Provider] Gemini Live API with native audio streaming")
    socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG)
