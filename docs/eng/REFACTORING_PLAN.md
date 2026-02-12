# Refactoring Plan for voice_agent.py

## Current Structure Issues

The current `voice_agent.py` is 1232 lines with everything in one file:
- Configuration and setup
- Session management classes
- WebSocket handlers
- Order processing logic
- Performance monitoring
- All mixed together

## Proposed Refactored Structure

```
voice_agent/
├── __init__.py
├── app.py                      # Main Flask app and routes
├── config.py                   # Configuration and constants
├── models/
│   ├── __init__.py
│   ├── session.py              # ConversationSession class
│   └── session_state.py        # SessionState enum
├── handlers/
│   ├── __init__.py
│   ├── chat_handler.py         # handle_chat with function calling
│   ├── recognition_handler.py  # ASR handlers
│   └── session_handler.py      # Session management handlers
├── services/
│   ├── __init__.py
│   ├── llm_service.py          # LLM interaction with function calling
│   ├── order_service.py        # Order processing logic
│   └── tts_service.py          # TTS streaming logic
└── utils/
    ├── __init__.py
    ├── data_loader.py          # Load menu, voices, etc.
    └── prompts.py              # System prompt generation
```

## Benefits

1. **Separation of Concerns**: Each module has a single responsibility
2. **Testability**: Easy to unit test individual components
3. **Maintainability**: Changes to one feature don't affect others
4. **Reusability**: Services can be reused across handlers
5. **Clarity**: Clear structure makes it easy to find code

## Key Refactorings

### 1. Extract LLM Service
```python
# services/llm_service.py
class LLMService:
    def __init__(self, openai_client, dashscope_client):
        self.openai_client = openai_client
        self.dashscope_client = dashscope_client

    def stream_with_function_calling(self, messages, tools, voice, session_id):
        """Stream LLM response with function calling"""
        # Returns: (content_buffer, tool_call_buffer)
```

### 2. Extract Order Service
```python
# services/order_service.py
class OrderService:
    @staticmethod
    def process_tool_call(tool_call, session):
        """Process update_order function call"""
        # Returns: order_update_result

    @staticmethod
    def calculate_totals(session):
        """Calculate order totals"""
        # Returns: (subtotal, tax, total)
```

### 3. Extract Prompt Builder
```python
# utils/prompts.py
class PromptBuilder:
    @staticmethod
    def build_function_calling_prompt(session, menu_items):
        """Build state-aware function calling prompt"""
        # Returns: prompt string
```

### 4. Simplify Chat Handler
```python
# handlers/chat_handler.py
def handle_chat(data):
    """Process chat message - now much simpler"""
    session = get_session(data)

    # Build prompt
    prompt = PromptBuilder.build_function_calling_prompt(session, menu_items)

    # Stream LLM
    content, tool_call = LLMService.stream_with_function_calling(...)

    # Process order
    if tool_call:
        OrderService.process_tool_call(tool_call, session)

    # Handle state transitions
    SessionService.check_state_transition(session, message)
```

## Implementation Steps

1. **Phase 1**: Extract configuration and constants
2. **Phase 2**: Extract models (Session, SessionState)
3. **Phase 3**: Extract services (LLM, Order, TTS)
4. **Phase 4**: Extract handlers
5. **Phase 5**: Update imports and test

## Would You Like Me To:

1. **Create the refactored structure** - I can create all the files with proper separation
2. **Just explain the approach** - Keep current structure but document it better
3. **Incremental refactoring** - Start with extracting one service at a time

Which approach would you prefer?
