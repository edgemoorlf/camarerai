"""
Configuration file for Voice Agent
Centralizes all configuration settings, API keys, and constants
"""

import os
from dotenv import load_dotenv
import httpx

load_dotenv()

# ============================================================================
# Provider Configuration
# ============================================================================

# Provider selection: 'dashscope', 'gemini', or 'gemini_live'
PROVIDER = os.getenv('PROVIDER', 'dashscope')

# Individual service providers (for future hybrid mode)
ASR_PROVIDER = os.getenv('ASR_PROVIDER', 'dashscope')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'dashscope')
TTS_PROVIDER = os.getenv('TTS_PROVIDER', 'dashscope')

# ============================================================================
# API Configuration
# ============================================================================

# DashScope Configuration
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
DASHSCOPE_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

# Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_LIVE_MODEL = os.getenv('GEMINI_LIVE_MODEL', 'gemini-2.5-flash-native-audio-latest')

# ============================================================================
# HTTP Session Configuration
# ============================================================================

def create_persistent_http_client():
    """Create a persistent HTTP client with connection pooling."""
    limits = httpx.Limits(
        max_connections=20,
        max_keepalive_connections=10,
        keepalive_expiry=60.0
    )
    return httpx.Client(limits=limits, timeout=httpx.Timeout(30.0, connect=5.0))

HTTP_CLIENT = create_persistent_http_client()

# ============================================================================
# Server Configuration
# ============================================================================

HOST = '0.0.0.0'
PORT = 5002
DEBUG = True
SECRET_KEY = os.urandom(24)

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

TAX_RATE = 0.09
MAX_TTS_LENGTH = 500
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
                            "name": {"type": "string", "description": "Name of the dish"},
                            "quantity": {"type": "integer", "description": "Quantity of the dish"},
                            "price": {"type": "number", "description": "Price per item"},
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
    IDLE = 'idle'
    ENROLLING = 'enrolling'
    ORDERING = 'ordering'
    CONFIRMED = 'confirmed'
    CONFIRMED_PASSIVE = 'confirmed_passive'
    CONFIRMED_STOPPED = 'confirmed_stopped'

# ============================================================================
# Configuration Validation
# ============================================================================

def validate_provider_config():
    """Validate provider configuration"""
    if PROVIDER == 'gemini' and not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY required when PROVIDER=gemini")
    if PROVIDER == 'gemini_live' and not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY required when PROVIDER=gemini_live")
    if PROVIDER == 'dashscope' and not DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY required when PROVIDER=dashscope")
    if PROVIDER not in ('dashscope', 'gemini', 'gemini_live'):
        raise ValueError(f"Invalid PROVIDER: {PROVIDER}")
