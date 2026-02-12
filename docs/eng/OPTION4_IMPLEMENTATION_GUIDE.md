# Option 4: Function Calling with Both Text and Tool Calls - CONFIRMED WORKING

**Date**: 2026-02-11
**Status**: ✅ FULLY VIABLE - Tested and confirmed working

---

## 🎉 Executive Summary

**Option 4 WORKS!** DashScope can return BOTH conversational text AND function calls in a single response, including in streaming mode.

### What We Discovered

With the right system prompt, the model will:
1. **First**: Stream conversational text (e.g., "好的，我帮您点一份麻婆豆腐。")
2. **Then**: Return structured function call with order data

This gives us the **best of all worlds**:
- ✅ Single LLM call (lower cost)
- ✅ Streaming conversational response (fast TTS)
- ✅ Structured order data (clean JSON)
- ✅ No ORDER_UPDATE pollution

---

## Test Results

### Non-Streaming Mode
```python
response = client.chat.completions.create(
    model='qwen-plus',
    messages=[
        {"role": "system", "content": "When customer orders: 1) Respond conversationally, 2) Call update_order function. Do BOTH."},
        {"role": "user", "content": "我要一份麻婆豆腐，价格是18元"}
    ],
    tools=[update_order_tool],
    tool_choice='auto'
)

# Result:
# ✅ message.content = "好的，我帮您点一份麻婆豆腐。"
# ✅ message.tool_calls = [update_order(...)]
```

### Streaming Mode
```python
stream = client.chat.completions.create(
    model='qwen-plus',
    messages=[...],  # Same as above
    tools=[update_order_tool],
    tool_choice='auto',
    stream=True
)

# Result:
# ✅ Streams content: "好的" → "，我帮" → "您点一份" → "麻婆豆腐" → "。"
# ✅ Then streams tool call: update_order with JSON arguments
```

**Perfect for TTS**: The conversational text streams first, so we can start TTS immediately!

---

## The Magic System Prompt

The key is explicitly instructing the model to do BOTH:

```python
SYSTEM_PROMPT = """You are a restaurant assistant. When a customer orders:

1. FIRST: Respond conversationally to acknowledge their order (e.g., "好的，我帮您点一份麻婆豆腐")
2. THEN: Call the update_order function with the order details

You MUST do BOTH steps in your response."""
```

### Why This Works

- **Explicit instruction**: The model knows it needs to do both actions
- **Order matters**: Text first, then function call
- **Clear expectation**: "You MUST do BOTH" ensures compliance

---

## Implementation for voice_agent.py

### Step 1: Define the Tool

```python
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
                            "price": {"type": "number", "description": "Price per item"}
                        },
                        "required": ["name", "quantity", "price"]
                    }
                }
            },
            "required": ["action", "items"]
        }
    }
}
```

### Step 2: Update System Prompt

```python
SYSTEM_PROMPT = """You are Emma, a friendly AI restaurant assistant at Golden Dragon Chinese Restaurant.

When customers order food:
1. FIRST: Respond conversationally to acknowledge their order in a natural, friendly way
2. THEN: Call the update_order function with the structured order details

You MUST do BOTH steps - respond conversationally AND call the function.

Menu items and prices:
- 麻婆豆腐 (Mapo Tofu): $18
- 宫保鸡丁 (Kung Pao Chicken): $20
- 糖醋里脊 (Sweet and Sour Pork): $22
...

Always be warm, helpful, and efficient."""
```

### Step 3: Streaming Implementation

```python
from openai import OpenAI

# Initialize OpenAI client pointing to DashScope
client = OpenAI(
    api_key=dashscope_api_key,
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
)

def handle_chat_streaming(session_id, message):
    """Handle chat with streaming and function calling"""

    session = sessions[session_id]
    session.add_message('user', message)

    # Get voice for this table
    voice = voices_data.get('tables', {}).get(session.table_id, 'Cherry')

    # Start streaming response
    stream = client.chat.completions.create(
        model='qwen-plus',
        messages=session.conversation_history,
        tools=[ORDER_UPDATE_TOOL],
        tool_choice='auto',
        stream=True
    )

    # Track what we receive
    content_buffer = ""
    sentence_buffer = ""
    tool_call_buffer = {"id": None, "name": None, "arguments": ""}

    # Notify client that streaming started
    emit('synthesis_started', {'session_id': session_id})

    for chunk in stream:
        delta = chunk.choices[0].delta

        # Handle conversational text (stream to TTS)
        if delta.content:
            content_buffer += delta.content
            sentence_buffer += delta.content

            # Send to client for display
            emit('llm_chunk', {
                'session_id': session_id,
                'text': delta.content
            })

            # Check for sentence ending
            if has_sentence_ending(sentence_buffer):
                sentence_to_synthesize = sentence_buffer.strip()[:500]

                print(f"[LLM→TTS] Streaming sentence: {sentence_to_synthesize[:50]}...")

                # Stream to TTS immediately
                for audio_chunk in dashscope_client.synthesize(
                    sentence_to_synthesize,
                    voice=voice,
                    stream=True
                ):
                    emit('audio_chunk', {
                        'session_id': session_id,
                        'chunk_type': audio_chunk['type'],
                        'audio_data': audio_chunk['data'],
                        'is_final': False
                    })

                # Send final marker for this sentence
                emit('audio_chunk', {
                    'session_id': session_id,
                    'is_final': True
                })

                sentence_buffer = ""

        # Handle tool calls (for order updates)
        if delta.tool_calls:
            for tc in delta.tool_calls:
                if tc.id:
                    tool_call_buffer["id"] = tc.id
                if tc.function.name:
                    tool_call_buffer["name"] = tc.function.name
                if tc.function.arguments:
                    tool_call_buffer["arguments"] += tc.function.arguments

    # Process any remaining sentence
    if sentence_buffer.strip():
        # ... (same TTS logic)

    # Process tool call if present
    if tool_call_buffer["name"]:
        print(f"[Function Call] {tool_call_buffer['name']}")

        try:
            import json
            arguments = json.loads(tool_call_buffer["arguments"])

            # Process order update
            if tool_call_buffer["name"] == "update_order":
                action = arguments.get("action")
                items = arguments.get("items", [])

                print(f"[Order] Action: {action}, Items: {len(items)}")

                # Update session order
                if action == "add":
                    for item in items:
                        session.current_order.append(item)
                        print(f"[Order] Added: {item['name']} x{item['quantity']} - ${item['price']}")

                # Calculate totals
                all_items = session.confirmed_items + session.current_order
                subtotal = sum(item['price'] * item['quantity'] for item in all_items)
                tax = subtotal * 0.09
                total = subtotal + tax

                # Send order update to client
                emit('order_updated', {
                    'session_id': session_id,
                    'confirmed_items': session.confirmed_items,
                    'current_order': session.current_order,
                    'action': action,
                    'subtotal': round(subtotal, 2),
                    'tax': round(tax, 2),
                    'total': round(total, 2)
                })

        except Exception as e:
            print(f"[Order] Error processing tool call: {e}")

    # Add assistant response to history
    session.add_message('assistant', content_buffer)
```

---

## Comparison: Option 4 vs Current Implementation

### Current Implementation (Option 2)
```python
# Single streaming call, ORDER_UPDATE in text
response = "好的，我帮您点一份麻婆豆腐。ORDER_UPDATE: {\"action\": \"add\", ...}"

# Problems:
# ❌ ORDER_UPDATE might go to TTS
# ❌ String parsing required
# ❌ Risk of malformed JSON
```

### Option 4 (Function Calling)
```python
# Single streaming call, clean separation
content = "好的，我帮您点一份麻婆豆腐。"  # → Goes to TTS
tool_call = {"name": "update_order", "arguments": {...}}  # → Goes to order processing

# Benefits:
# ✅ No ORDER_UPDATE in text stream
# ✅ Structured JSON (type-safe)
# ✅ Clean separation of concerns
# ✅ Same cost as current (single call)
```

---

## Performance Comparison

### Option 1: Two Sequential Calls
```
ASR:              ~500ms
LLM Call 1:       ~800ms (function calling)
LLM Call 2:       ~800ms (streaming conversation)
TTS First Audio:  ~300ms
-----------------------------------
Total:            ~2400ms
Cost:             2x LLM calls
```

### Option 4: Single Call with Function Calling
```
ASR:              ~500ms
LLM Call:         ~800ms (streaming with function calling)
TTS First Audio:  ~300ms
-----------------------------------
Total:            ~1600ms ✅ Same as current!
Cost:             1x LLM call ✅ Same as current!
```

**Option 4 has the SAME performance and cost as the current implementation, but with clean separation!**

---

## Migration Path

### Phase 1: Add Function Calling (Parallel with Current)
1. Add `ORDER_UPDATE_TOOL` definition
2. Update system prompt to include function calling instruction
3. Add tool call processing logic
4. Keep current ORDER_UPDATE parsing as fallback

### Phase 2: Test and Validate
1. Test with various order scenarios
2. Verify tool calls are always made
3. Verify conversational text is always present
4. Monitor for any edge cases

### Phase 3: Remove Old Implementation
1. Remove ORDER_UPDATE string parsing
2. Remove ORDER_UPDATE detection in stream
3. Simplify code

---

## Edge Cases and Handling

### What if model doesn't call the function?
- **Fallback**: Keep current ORDER_UPDATE parsing as backup
- **Monitoring**: Log when function calls are missing
- **Prompt tuning**: Strengthen "You MUST call the function" instruction

### What if model doesn't provide text?
- **Fallback**: Generate default acknowledgment (e.g., "好的！")
- **Monitoring**: Log when content is missing
- **Prompt tuning**: Strengthen "You MUST respond conversationally" instruction

### What if function arguments are invalid?
- **Validation**: JSON schema validation
- **Error handling**: Log error, ask user to clarify
- **Fallback**: Don't update order, ask for confirmation

---

## Recommended Next Steps

1. **Implement in voice_agent.py**:
   - Add `ORDER_UPDATE_TOOL` definition
   - Update system prompt
   - Add function call processing in streaming handler
   - Keep current ORDER_UPDATE parsing as fallback

2. **Test thoroughly**:
   - Test with various order scenarios
   - Test edge cases (no function call, no text, invalid args)
   - Monitor logs for any issues

3. **Monitor in production**:
   - Track function call success rate
   - Track text response presence
   - Monitor for any parsing errors

4. **Optimize**:
   - Fine-tune system prompt for better compliance
   - Add more robust error handling
   - Remove fallback code once stable

---

## Conclusion

**Option 4 is the optimal solution**:
- ✅ Clean separation (no ORDER_UPDATE in text)
- ✅ Type-safe structured data
- ✅ Same performance as current implementation
- ✅ Same cost as current implementation
- ✅ Works in streaming mode
- ✅ Easy to implement

**Recommendation**: Implement Option 4 as the primary approach, with current ORDER_UPDATE parsing as fallback during transition period.

---

## Code Example: Complete Implementation

See `/tmp/test_option4_streaming_both.py` for working example.

Key takeaways:
1. Use OpenAI-compatible API for DashScope
2. Include explicit instruction in system prompt
3. Process content chunks for TTS
4. Process tool call chunks for order updates
5. Both come in the same streaming response!
