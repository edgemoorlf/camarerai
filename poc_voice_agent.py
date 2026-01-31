"""
CamareraI - POC Voice Agent
Main Flask application for restaurant voice ordering
"""

from flask import Flask, render_template, request, jsonify, send_file
from dashscope_client import DashScopeClient
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize DashScope client
dashscope_client = DashScopeClient()

# In-memory session storage (for POC)
sessions = {}

# Load restaurant data
def load_json_data(filename):
    """Load JSON data from data directory"""
    filepath = os.path.join('data', filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Load data files
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
        self.role = role  # 'customer', 'owner', 'staff'
        self.language = 'en'  # Auto-detected
        self.party_size = None
        self.dietary_restrictions = []
        self.current_order = []
        self.conversation_history = []
        self.created_at = datetime.now()
        self.speakers = {}  # Track individual speakers

    def _assign_table_name(self):
        """Assign a unique table name (e.g., 'Table 5 - Lily')"""
        names = table_names.get('names', ['Lily', 'Emma', 'Sophie', 'Grace'])
        # Simple assignment based on table_id
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
        return message

    def get_system_prompt(self):
        """Generate role-specific system prompt"""
        restaurant_name = menu_data.get('restaurant', {}).get('name', 'Golden Dragon')

        if self.role == 'customer':
            return f"""You are {self.table_name.split(' - ')[1]}, a friendly AI assistant at {restaurant_name}.
Help customers order food naturally. Speak in their language (English, Mandarin, or Cantonese).

Current context:
- Table: {self.table_name}
- Party size: {self.party_size or 'unknown'}
- Dietary restrictions: {', '.join(self.dietary_restrictions) or 'none'}
- Current order: {len(self.current_order)} items

Menu highlights:
{self._get_menu_summary()}

Guidelines:
- Be conversational and warm
- Ask about dietary restrictions if not known
- Suggest popular items and staff recommendations
- Confirm quantities and modifications
- Keep responses concise (2-3 sentences)
- If unsure, ask clarifying questions
"""
        elif self.role == 'owner':
            return f"""You are {self.table_name.split(' - ')[1]}, assistant to the owner of {restaurant_name}.
Provide business insights and help manage the restaurant.
Speak in their language (English, Mandarin, or Cantonese).

Today's context:
- Active tables: {len(sessions)}
- Total orders: {sum(len(s.current_order) for s in sessions.values())}
"""
        else:  # staff
            return f"""You are {self.table_name.split(' - ')[1]}, assistant to the staff at {restaurant_name}.
Help with order details and table management.
Speak in their language (English, Mandarin, or Cantonese).

Current orders: {len(self.current_order)} items
"""

    def _get_menu_summary(self):
        """Get a concise menu summary for the prompt"""
        menu = menu_data.get('menu', {})
        summary = []

        for category, items in menu.items():
            if items and len(items) > 0:
                # Show top 3 items per category
                top_items = items[:3]
                for item in top_items:
                    name = item.get('name', {})
                    if isinstance(name, dict):
                        name_str = f"{name.get('en', '')} ({name.get('zh', '')})"
                    else:
                        name_str = name
                    price = item.get('price', 0)
                    summary.append(f"- {name_str}: ${price}")

        return '\n'.join(summary[:10])  # Limit to 10 items


@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')


@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new conversation session"""
    data = request.json
    table_id = data.get('table_id', '1')
    role = data.get('role', 'customer')

    session = ConversationSession(table_id, role)
    sessions[session.session_id] = session

    return jsonify({
        'session_id': session.session_id,
        'table_name': session.table_name,
        'role': role
    })


@app.route('/api/voice/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio to text"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    session_id = request.form.get('session_id')

    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    try:
        # Save audio temporarily
        temp_path = f'/tmp/{uuid.uuid4()}.wav'
        audio_file.save(temp_path)

        # Transcribe using DashScope
        text = dashscope_client.transcribe(temp_path)

        # Clean up
        os.remove(temp_path)

        return jsonify({
            'text': text,
            'session_id': session_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat message and generate response"""
    data = request.json
    session_id = data.get('session_id')
    message = data.get('message')

    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    session = sessions[session_id]

    try:
        # Add user message to history
        session.add_message('user', message)

        # Build messages for LLM
        messages = [
            {'role': 'system', 'content': session.get_system_prompt()}
        ]

        # Add recent conversation history (last 10 messages)
        for msg in session.conversation_history[-10:]:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })

        # Get AI response
        response = dashscope_client.chat(messages)

        # Add AI response to history
        session.add_message('assistant', response)

        return jsonify({
            'response': response,
            'session_id': session_id,
            'table_name': session.table_name
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/synthesize', methods=['POST'])
def synthesize_speech():
    """Convert text to speech"""
    data = request.json
    text = data.get('text')
    session_id = data.get('session_id')

    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400

    session = sessions[session_id]

    try:
        # Get voice ID for this table (if cloned)
        voice_id = voices_data.get('tables', {}).get(session.table_id)

        # Synthesize speech
        audio_url = dashscope_client.synthesize(text, voice_id=voice_id)

        return jsonify({
            'audio_url': audio_url,
            'session_id': session_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        'conversation_history': session.conversation_history[-20:]  # Last 20 messages
    })


if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)

    print("="*60)
    print("CamareraI - Voice Agent POC")
    print("="*60)
    print(f"Restaurant: {menu_data.get('restaurant', {}).get('name', 'Not loaded')}")
    print(f"Menu items: {sum(len(items) for items in menu_data.get('menu', {}).values())}")
    print("="*60)

    app.run(debug=True, host='0.0.0.0', port=5002)
