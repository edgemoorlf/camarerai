# Voice Agent Refactoring - Detailed Explanation

## How Option 4 Function Calling Works

### The 3-Part System

**1. Tool Definition** (What the LLM can call)
```python
ORDER_UPDATE_TOOL = {
    "type": "function",
    "function": {
        "name": "update_order",
        "parameters": {...}  # JSON schema
    }
}
```

**2. System Prompt** (Instructions to call it)
```
"When customer orders, you MUST do TWO things:
1. Respond conversationally
2. Call update_order function"
```

**3. Stream Processing** (Handle the response)
```python
for chunk in stream:
    if delta.content:      # Conversational text
        → Stream to TTS
    if delta.tool_calls:   # Function call
        → Update order
```

---

## Refactoring Approach

I recommend **incremental refactoring** - extract one service at a time while keeping the system working.

### Step 1: Extract Configuration (Easiest)

Create `config.py`:
```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
DASHSCOPE_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

# Server Configuration
HOST = '0.0.0.0'
PORT = 5002
DEBUG = True

# Order Configuration
TAX_RATE = 0.09
MAX_TTS_LENGTH = 500

# Tool Definition
ORDER_UPDATE_TOOL = {
    "type": "function",
    "function": {
        "name": "update_order",
        "description": "Update the customer's food order",
        "parameters": {...}
    }
}
```

### Step 2: Extract Order Processing Logic

Create `services/order_service.py`:
```python
# services/order_service.py
class OrderService:
    """Handles order processing logic"""

    @staticmethod
    def process_tool_call(tool_call_buffer, session):
        """Process update_order function call"""
        if tool_call_buffer["name"] != "update_order":
            return None

        arguments = json.loads(tool_call_buffer["arguments"])
        action = arguments.get("action")
        items = arguments.get("items", [])

        if session.state == SessionState.CONFIRMED:
            return OrderService._process_confirmed_state(action, items, session)
        elif session.state == SessionState.ORDERING:
            return OrderService._process_ordering_state(action, items, session)

    @staticmethod
    def _process_ordering_state(action, items, session):
        """Process order in ORDERING state"""
        if action == 'add':
            for item in items:
                session.current_order.append(item)
        elif action == 'remove':
            for item in items:
                item_name = item['name'].lower()
                session.current_order = [
                    o for o in session.current_order
                    if o['name'].lower() != item_name
                ]
        elif action == 'modify':
            # ... modify logic

        return OrderService.calculate_totals(session)

    @staticmethod
    def calculate_totals(session):
        """Calculate order totals"""
        all_items = session.confirmed_items + session.current_order
        subtotal = sum(item['price'] * item['quantity'] for item in all_items)
        tax = subtotal * 0.09
        total = subtotal + tax

        return {
            'subtotal': round(subtotal, 2),
            'tax': round(tax, 2),
            'total': round(total, 2),
            'item_count': len(all_items)
        }
```

### Step 3: Extract LLM Streaming Logic

Create `services/llm_service.py`:
```python
# services/llm_service.py
class LLMService:
    """Handles LLM interaction with function calling"""

    def __init__(self, openai_client, dashscope_client, perf_monitor):
        self.openai_client = openai_client
        self.dashscope_client = dashscope_client
        self.perf_monitor = perf_monitor

    def stream_with_function_calling(self, messages, tools, voice, session_id, emit_func):
        """
        Stream LLM response with function calling

        Returns:
            tuple: (content_buffer, tool_call_buffer)
        """
        # Start performance tracking
        self.perf_monitor.start_timer('llm')
        self.perf_monitor.mark_event('llm_start')

        # Create stream
        stream = self.openai_client.chat.completions.create(
            model='qwen-plus',
            messages=messages,
            tools=tools,
            tool_choice='auto',
            stream=True
        )

        # Process stream
        content_buffer = ""
        sentence_buffer = ""
        tool_call_buffer = {"id": None, "name": None, "arguments": ""}

        emit_func('llm_started', {'session_id': session_id})

        for chunk in stream:
            delta = chunk.choices[0].delta

            # Handle content
            if delta.content:
                if not content_buffer:
                    self.perf_monitor.mark_event('llm_first_chunk')

                content_buffer += delta.content
                sentence_buffer += delta.content

                emit_func('llm_chunk', {
                    'session_id': session_id,
                    'text': delta.content
                })

                # Stream to TTS when sentence ends
                if has_sentence_ending(sentence_buffer):
                    self._stream_to_tts(sentence_buffer, voice, session_id, emit_func)
                    sentence_buffer = ""

            # Handle tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if tc.id:
                        tool_call_buffer["id"] = tc.id
                    if tc.function.name:
                        tool_call_buffer["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_call_buffer["arguments"] += tc.function.arguments

        # Process remaining sentence
        if sentence_buffer.strip():
            self._stream_to_tts(sentence_buffer, voice, session_id, emit_func)

        return content_buffer, tool_call_buffer

    def _stream_to_tts(self, text, voice, session_id, emit_func):
        """Stream text to TTS"""
        sentence = text.strip()[:500]

        self.perf_monitor.mark_event('tts_start')
        emit_func('synthesis_started', {'session_id': session_id})

        try:
            chunk_count = 0
            for audio_chunk in self.dashscope_client.synthesize(
                sentence, voice=voice, language_type='Auto', stream=True
            ):
                if chunk_count == 0:
                    self.perf_monitor.mark_event('first_audio')

                chunk_count += 1
                emit_func('audio_chunk', {
                    'session_id': session_id,
                    'chunk_type': audio_chunk['type'],
                    'audio_data': audio_chunk['data'],
                    'chunk_number': chunk_count,
                    'is_final': False
                })

            emit_func('audio_chunk', {'session_id': session_id, 'is_final': True})
        except Exception as e:
            print(f"[TTS] Error: {e}")
```

### Step 4: Extract Prompt Builder

Create `utils/prompts.py`:
```python
# utils/prompts.py
class PromptBuilder:
    """Builds system prompts for different states"""

    @staticmethod
    def build_function_calling_prompt(session, menu_items):
        """Build state-aware function calling prompt"""
        if session.state == SessionState.ORDERING:
            return PromptBuilder._build_ordering_prompt(session, menu_items)
        elif session.state == SessionState.CONFIRMED:
            return PromptBuilder._build_confirmed_prompt(session, menu_items)
        else:
            return ""

    @staticmethod
    def _build_ordering_prompt(session, menu_items):
        """Build prompt for ORDERING state"""
        menu_list = '\n'.join([
            f"- {item['en']} / {item['zh']} / {item['yue']}: ${item['price']}"
            for item in menu_items[:15]
        ])

        current_order = '\n'.join([
            f"- {item['name']} x{item['quantity']}"
            for item in session.current_order
        ]) if session.current_order else "No items yet"

        return f"""
IMPORTANT: When customer orders items, you MUST do TWO things:

1. FIRST: Respond conversationally to acknowledge their order
2. THEN: Call the update_order function with the structured order details

You MUST do BOTH steps in your response.

Available menu items:
{menu_list}

Current order ({len(session.current_order)} items):
{current_order}

CRITICAL RULES:
1. ONLY call update_order when customer EXPLICITLY orders items
2. DO NOT call update_order when making recommendations
3. Customer must use ordering language like "我要...", "I'll have..."
4. For removals, customer must use "取消...", "Cancel..."
5. ALWAYS call update_order for removals
"""

    @staticmethod
    def _build_confirmed_prompt(session, menu_items):
        """Build prompt for CONFIRMED state"""
        # Similar structure for confirmed state
        pass
```

### Step 5: Simplified Chat Handler

Now `handle_chat` becomes much simpler:

```python
# handlers/chat_handler.py
from services.llm_service import LLMService
from services.order_service import OrderService
from utils.prompts import PromptBuilder
from config import ORDER_UPDATE_TOOL

def handle_chat(data, llm_service, order_service):
    """Process chat message with function calling"""
    session_id = data.get('session_id')
    message = data.get('message')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    session = sessions[session_id]

    try:
        # Add user message
        session.add_message('user', message)

        # Build prompt
        system_prompt = session.get_system_prompt()
        function_prompt = PromptBuilder.build_function_calling_prompt(
            session, menu_items_list
        )

        messages = [
            {'role': 'system', 'content': system_prompt + '\n\n' + function_prompt}
        ]
        messages.extend(session.conversation_history[-10:])

        # Get voice
        voice = voices_data.get('tables', {}).get(session.table_id, 'Cherry')

        # Stream LLM with function calling
        content, tool_call = llm_service.stream_with_function_calling(
            messages=messages,
            tools=[ORDER_UPDATE_TOOL],
            voice=voice,
            session_id=session_id,
            emit_func=emit
        )

        # Process tool call
        if tool_call["name"]:
            order_result = order_service.process_tool_call(tool_call, session)

            if order_result:
                emit('order_updated', {
                    'session_id': session_id,
                    'confirmed_items': session.confirmed_items,
                    'current_order': session.current_order,
                    **order_result
                })

        # Check state transitions
        if session._is_closing_remark(message):
            handle_state_transition(session, session_id)

        # Record metrics
        perf_monitor.end_timer('llm')
        perf_monitor.record_request()
        emit('performance_metrics', {
            'session_id': session_id,
            'metrics': perf_monitor.get_metrics_for_client()
        })

        # Add response to history
        session.add_message('assistant', content)

        emit('chat_response', {
            'session_id': session_id,
            'response': content,
            'table_name': session.table_name
        })

    except Exception as e:
        print(f"[Chat] Error: {e}")
        emit('error', {'message': f'Chat error: {str(e)}'})
```

---

## Benefits of This Refactoring

### Before (Monolithic)
- 1232 lines in one file
- Hard to test individual components
- Changes affect multiple concerns
- Difficult to understand flow

### After (Modular)
- ~200 lines per file
- Easy to unit test each service
- Changes isolated to specific modules
- Clear separation of concerns

---

## Would You Like Me To:

1. **Implement the full refactoring** - Create all the files and migrate the code
2. **Start with one service** - Extract just OrderService or LLMService first
3. **Keep current structure** - Just add better documentation and comments

Let me know which approach you prefer!
