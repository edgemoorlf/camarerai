"""
Voice Agent - Gemini Standard API Implementation
Uses Gemini 1.5 Flash for ASR + LLM, DashScope for TTS
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
import base64
import io

import config
from models.conversation_session import ConversationSession
from routes.api import load_json_data, register_routes
from services.order_service import OrderService
from services.gemini_standard_service import GeminiStandardService
from services.dashscope_service import DashScopeService
from performance_monitor import PerformanceMetrics


# ============================================================================
# Initialize Services
# ============================================================================

perf_monitor = PerformanceMetrics(max_history=config.MAX_PERFORMANCE_HISTORY)
order_service = OrderService()
gemini_service = GeminiStandardService(perf_monitor)
dashscope_service = DashScopeService()

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
audio_buffers = {}  # session_id -> accumulated audio bytes


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
    if session_id in audio_buffers:
        del audio_buffers[session_id]


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
    """Start audio accumulation for recognition"""
    session_id = data.get('session_id')

    if session_id not in sessions:
        emit('error', {'message': 'Session not found'})
        return

    # Initialize audio buffer for this session
    audio_buffers[session_id] = io.BytesIO()

    # Start performance tracking
    perf_monitor.start_timer('asr')

    emit('recognition_started', {'session_id': session_id})
    print(f"[ASR] Started audio accumulation for session {session_id}")


@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle audio data from client - accumulate for batch processing"""
    session_id = data.get('session_id')
    audio_base64 = data.get('audio')

    if not session_id or not audio_base64:
        return

    if session_id not in audio_buffers:
        return

    try:
        # Decode base64 audio and accumulate
        audio_bytes = base64.b64decode(audio_base64)
        audio_buffers[session_id].write(audio_bytes)
    except Exception as e:
        print(f"[Audio] Error processing audio: {e}")


@socketio.on('stop_recognition')
def handle_stop_recognition(data):
    """Process accumulated audio with Gemini"""
    session_id = data.get('session_id')

    if session_id not in sessions:
        emit('error', {'message': 'Session not found'})
        return

    if session_id not in audio_buffers:
        emit('recognition_stopped', {'session_id': session_id})
        return

    try:
        # Get accumulated audio
        audio_bytes = audio_buffers[session_id].getvalue()
        del audio_buffers[session_id]

        print(f"[ASR] Processing {len(audio_bytes)} bytes of audio")

        # Process with Gemini
        session = sessions[session_id]
        result = gemini_service.process_audio(
            audio_bytes,
            mime_type='audio/webm',
            session=session,
            menu_data=menu_data
        )

        # Mark ASR complete
        perf_monitor.end_timer('asr')
        perf_monitor.mark_event('asr_complete')

        transcript = result.get('text', '')
        language_code = result.get('language_code', 'en-US')

        print(f"[ASR] Transcript: {transcript}")

        # Emit transcript to client
        emit('transcript', {
            'session_id': session_id,
            'text': transcript,
            'is_final': True,
            'language': language_code
        })

        # Add to conversation history
        if transcript:
            session.add_message('user', transcript)

            # Process with TTS
            process_tts(session_id, transcript, result.get('text', ''), language_code)

    except Exception as e:
        print(f"[ASR] Error processing audio: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'ASR error: {str(e)}'})

    emit('recognition_stopped', {'session_id': session_id})


def process_tts(session_id, transcript, response_text, language_code):
    """Process TTS for Gemini response"""
    if not response_text:
        return

    session = sessions[session_id]

    # Add assistant response to history
    session.add_message('assistant', response_text)

    # Determine voice based on language
    voice_map = {
        'en-US': 'Cherry',
        'cmn-CN': 'Sicheng',
        'yue-HK': 'Sicheng'
    }
    voice = voice_map.get(language_code, 'Cherry')

    # Emit synthesis started
    emit('synthesis_started', {'session_id': session_id})
    perf_monitor.start_timer('tts')

    try:
        chunk_count = 0
        first_chunk = True

        for audio_chunk in dashscope_service.synthesize(
            response_text[:config.MAX_TTS_LENGTH],
            voice=voice,
            language_type='Auto',
            stream=True
        ):
            if first_chunk:
                perf_monitor.mark_event('first_audio')
                first_chunk = False

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

        perf_monitor.end_timer('tts')
        perf_monitor.record_request()

        print(f"[TTS] Completed: {chunk_count} chunks")

    except Exception as e:
        print(f"[TTS] Error: {e}")
        emit('error', {'message': f'TTS error: {str(e)}'})


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

    # Process with Gemini
    try:
        result = gemini_service.process_text(
            message,
            session=session,
            menu_data=menu_data
        )

        response_text = result.get('text', '')
        language_code = result.get('language_code', 'en-US')

        # Process TTS
        process_tts(session_id, message, response_text, language_code)

    except Exception as e:
        print(f"[Chat] Error: {e}")
        emit('error', {'message': f'Chat error: {str(e)}'})


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
    print(f"[Server] Starting Gemini Standard Voice Agent on {config.HOST}:{config.PORT}")
    print(f"[Provider] Gemini Standard API + DashScope TTS")
    socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG)
