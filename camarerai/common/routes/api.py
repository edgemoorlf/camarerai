"""
API Routes for Voice Agent
Shared HTTP routes that work with all providers
"""

import json
import os
from flask import jsonify, request
from camarerai import config


def load_json_data(filename, data_dir=config.DATA_DIR):
    """Load JSON data from file"""
    filepath = os.path.join(data_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found, using empty dict")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not parse {filepath}")
        return {}


def register_routes(app, sessions, menu_data, knowledge_data, voices_data, table_names):
    """Register all API routes with the Flask app"""

    @app.route('/api/menu')
    def get_menu():
        """Get menu data"""
        return jsonify(menu_data)

    @app.route('/api/knowledge')
    def get_knowledge():
        """Get restaurant knowledge base"""
        return jsonify(knowledge_data)

    @app.route('/api/session/<session_id>')
    def get_session(session_id):
        """Get session details"""
        if session_id in sessions:
            return jsonify(sessions[session_id].to_dict())
        return jsonify({'error': 'Session not found'}), 404

    @app.route('/api/sessions')
    def get_all_sessions():
        """Get all active sessions"""
        return jsonify({
            sid: session.to_dict()
            for sid, session in sessions.items()
        })

    @app.route('/api/session/<session_id>/order', methods=['GET'])
    def get_order(session_id):
        """Get order for a session"""
        if session_id in sessions:
            return jsonify(sessions[session_id].get_order_summary())
        return jsonify({'error': 'Session not found'}), 404

    @app.route('/api/voices')
    def get_voices():
        """Get available TTS voices"""
        return jsonify(voices_data)

    @app.route('/api/config')
    def get_config():
        """Get provider configuration"""
        return jsonify({
            'provider': config.PROVIDER,
            'asr_provider': config.ASR_PROVIDER,
            'llm_provider': config.LLM_PROVIDER,
            'tts_provider': config.TTS_PROVIDER,
            'host': config.HOST,
            'port': config.PORT
        })

    @app.route('/api/table_names')
    def get_table_names():
        """Get available table names"""
        return jsonify(table_names)
