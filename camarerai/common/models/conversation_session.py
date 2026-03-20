"""
Conversation Session Model
Manages a conversation session for a table
"""

import uuid
from datetime import datetime
from camarerai import config


class ConversationSession:
    """Manages a conversation session for a table"""

    def __init__(self, table_id, role='customer', table_names=None):
        self.session_id = str(uuid.uuid4())
        self.table_id = table_id
        self.table_names = table_names or {}
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
        names = self.table_names.get('names', ['Lily', 'Emma', 'Sophie', 'Grace'])
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

    def get_messages_for_llm(self, limit=20):
        """Get recent messages formatted for LLM"""
        recent = self.conversation_history[-limit:]
        return [{'role': m['role'], 'content': m['content']} for m in recent]

    def add_order_item(self, item):
        """Add an item to the current order"""
        self.current_order.append(item)
        self.last_activity = datetime.now()

    def remove_order_item(self, item_index):
        """Remove an item from the current order"""
        if 0 <= item_index < len(self.current_order):
            removed = self.current_order.pop(item_index)
            self.last_activity = datetime.now()
            return removed
        return None

    def modify_order_item(self, item_index, modifications):
        """Modify an item in the current order"""
        if 0 <= item_index < len(self.current_order):
            self.current_order[item_index].update(modifications)
            self.last_activity = datetime.now()
            return self.current_order[item_index]
        return None

    def confirm_order(self):
        """Confirm the current order"""
        self.confirmed_items.extend(self.current_order)
        self.current_order = []
        self.order_confirmed_at = datetime.now()
        self.state = config.SessionState.CONFIRMED
        self.last_activity = datetime.now()

    def get_all_items(self):
        """Get all items (confirmed + current)"""
        return self.confirmed_items + self.current_order

    def get_order_summary(self):
        """Get a summary of the order"""
        items = self.get_all_items()
        total = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
        return {
            'items': items,
            'total': total,
            'item_count': len(items)
        }

    def to_dict(self):
        """Convert session to dictionary for serialization"""
        return {
            'session_id': self.session_id,
            'table_id': self.table_id,
            'table_name': self.table_name,
            'role': self.role,
            'language': self.language,
            'party_size': self.party_size,
            'dietary_restrictions': self.dietary_restrictions,
            'state': self.state,
            'current_order': self.current_order,
            'confirmed_items': self.confirmed_items,
            'order_confirmed_at': self.order_confirmed_at.isoformat() if self.order_confirmed_at else None,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }
