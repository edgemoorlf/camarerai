"""
Configuration file for Voice Agent
Centralizes all configuration settings, API keys, and constants
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# API Configuration
# ============================================================================

DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
DASHSCOPE_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

# ============================================================================
# Server Configuration
# ============================================================================

HOST = '0.0.0.0'
PORT = 5002
DEBUG = True

# Flask configuration
SECRET_KEY = os.urandom(24)

# SocketIO configuration
SOCKETIO_CONFIG = {
    'cors_allowed_origins': "*",
    'async_mode': 'threading',
    'engineio_logger': False,
    'logger': False,
    'ping_timeout': 60,
    'ping_interval': 25
}

# ============================================================================
# Business Logic Configuration
# ============================================================================

# Tax rate for order calculations
TAX_RATE = 0.09

# Maximum text length for TTS (characters)
MAX_TTS_LENGTH = 500

# Performance monitoring
MAX_PERFORMANCE_HISTORY = 100

# ============================================================================
# Data File Paths
# ============================================================================

DATA_DIR = 'data'
MENU_FILE = 'menu.json'
KNOWLEDGE_FILE = 'knowledge.json'
TABLE_NAMES_FILE = 'table_names.json'
VOICES_FILE = 'voices.json'

# ============================================================================
# Function Calling Tool Definition
# ============================================================================

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

# ============================================================================
# Session State Constants
# ============================================================================

class SessionState:
    """Session state constants"""
    IDLE = 'idle'
    ENROLLING = 'enrolling'
    ORDERING = 'ordering'
    CONFIRMED = 'confirmed'
    CONFIRMED_PASSIVE = 'confirmed_passive'  # Passive listening (no AI response)
    CONFIRMED_STOPPED = 'confirmed_stopped'  # Listening stopped
