# Option 4: Function Calling - How It Works

## Overview

Option 4 uses **function calling** (also called tool use) to cleanly separate conversational responses from structured order data. The LLM returns BOTH in a single streaming response.

---

## The Flow

```
User says: "我要一份麻婆豆腐"
    ↓
1. System prompt tells LLM: "Do TWO things: respond conversationally AND call update_order function"
    ↓
2. LLM streams response with BOTH parts:
   - Content: "好的，我帮您点一份麻婆豆腐。"
   - Tool call: update_order({"action": "add", "items": [...]})
    ↓
3. We process the stream:
   - Content chunks → Stream to TTS immediately
   - Tool call chunks → Buffer for order processing
    ↓
4. After streaming completes:
   - User hears the response (from TTS)
   - Order UI updates (from tool call)
```

---

## Key Components

### 1. Tool Definition (Lines 52-97)

```python
ORDER_UPDATE_TOOL = {
    "type": "function",
    "function": {
        "name": "update_order",
        "description": "Update the customer's food order",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "modify", "remove"]},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "price": {"type": "number"}
                        }
                    }
                }
            }
        }
    }
}
```

**What this does**: Defines the schema for the `update_order` function. The LLM knows:
- Function name: `update_order`
- What it does: Updates the order
- What parameters it needs: action (add/modify/remove) and items (array of dishes)

### 2. System Prompt (Lines 340-360)

```python
function_calling_prompt = """
IMPORTANT: When customer orders items, you MUST do TWO things:

1. FIRST: Respond conversationally to acknowledge their order
2. THEN: Call the update_order function with the structured order details

You MUST do BOTH steps in your response.
"""
```

**What this does**: Explicitly tells the LLM to:
- Respond with conversational text (for the customer to hear)
- Call the function (for structured data)
- Do BOTH, not just one

### 3. Streaming Request (Lines 405-411)

```python
stream = openai_client.chat.completions.create(
    model='qwen-plus',
    messages=messages,
    tools=[ORDER_UPDATE_TOOL],  # ← Pass the tool definition
    tool_choice='auto',          # ← Let model decide when to call
    stream=True                  # ← Stream the response
)
```

**What this does**:
- Sends request to LLM with tool definition
- `tool_choice='auto'` means model decides when to call the function
- `stream=True` means we get chunks progressively

### 4. Processing the Stream (Lines 421-490)

```python
for chunk in stream:
    delta = chunk.choices[0].delta

    # Handle conversational text
    if delta.content:
        content_buffer += delta.content
        sentence_buffer += delta.content

        # Stream to TTS when sentence ends
        if has_sentence_ending(sentence_buffer):
            # → Send to TTS immediately

    # Handle tool calls
    if delta.tool_calls:
        tool_call_buffer["arguments"] += tc.function.arguments
```

**What this does**:
- **Content chunks**: Accumulate and stream to TTS sentence-by-sentence
- **Tool call chunks**: Buffer the function arguments

### 5. Processing Tool Call (Lines 520-600)

```python
if tool_call_buffer["name"] == "update_order":
    arguments = json.loads(tool_call_buffer["arguments"])
    action = arguments.get("action")
    items = arguments.get("items", [])

    if action == 'add':
        for item in items:
            session.current_order.append(item)
    elif action == 'remove':
        # Remove items from order
    elif action == 'modify':
        # Modify item quantities
```

**What this does**: After streaming completes, parse the tool call and update the order.

---

## Example Response

### User Input
```
"我要一份麻婆豆腐，价格是18元"
```

### LLM Response (Streaming)
```json
{
  "choices": [{
    "delta": {
      "content": "好的",  // ← Chunk 1: content
      "tool_calls": null
    }
  }]
}

{
  "choices": [{
    "delta": {
      "content": "，我帮您点一份",  // ← Chunk 2: content
      "tool_calls": null
    }
  }]
}

{
  "choices": [{
    "delta": {
      "content": "麻婆豆腐。",  // ← Chunk 3: content (sentence ends!)
      "tool_calls": null
    }
  }]
}

{
  "choices": [{
    "delta": {
      "content": null,
      "tool_calls": [{  // ← Chunk 4: tool call starts
        "function": {
          "name": "update_order",
          "arguments": "{\"action\": \"add\""
        }
      }]
    }
  }]
}

{
  "choices": [{
    "delta": {
      "content": null,
      "tool_calls": [{  // ← Chunk 5: tool call continues
        "function": {
          "arguments": ", \"items\": [{\"name\": \"麻婆豆腐\""
        }
      }]
    }
  }]
}

// ... more chunks until complete
```

### What We Do With It

1. **Content chunks** → "好的，我帮您点一份麻婆豆腐。"
   - Stream to TTS immediately
   - User hears the response

2. **Tool call chunks** → `update_order({"action": "add", "items": [...]})`
   - Buffer and parse after streaming
   - Update order UI

---

## Why This Works

### 1. Clean Separation
- **Text stream**: Never contains ORDER_UPDATE or JSON
- **Tool call**: Pure structured data
- No risk of TTS speaking JSON

### 2. Single LLM Call
- Not two separate calls
- Same cost and latency as before
- Model returns both in one response

### 3. Streaming Still Works
- Content streams first (usually)
- Tool call comes after
- TTS starts immediately when first sentence completes

---

## Comparison

### Before (Option 2 - String Parsing)
```python
# LLM returns mixed text
response = "好的，我帮您点一份麻婆豆腐。ORDER_UPDATE: {\"action\": \"add\", ...}"

# We had to:
1. Detect "ORDER_UPDATE:" in stream
2. Stop TTS before it reaches ORDER_UPDATE
3. Parse JSON from string
4. Risk: ORDER_UPDATE might go to TTS
```

### After (Option 4 - Function Calling)
```python
# LLM returns separated data
content = "好的，我帮您点一份麻婆豆腐。"  # → TTS
tool_call = {"name": "update_order", "arguments": {...}}  # → Order processing

# We just:
1. Stream content to TTS
2. Buffer tool call
3. Parse structured JSON
4. No risk: ORDER_UPDATE never in text
```

---

## The Magic Prompt

The key to making this work is the system prompt:

```
IMPORTANT: When customer orders items, you MUST do TWO things:

1. FIRST: Respond conversationally to acknowledge their order
2. THEN: Call the update_order function with the structured order details

You MUST do BOTH steps in your response.
```

Without this explicit instruction, the model would choose to EITHER:
- Respond with text, OR
- Call the function

But NOT both. The prompt tells it to do BOTH.

---

## Benefits

1. **Type Safety**: JSON schema validation
2. **No Pollution**: ORDER_UPDATE never in text
3. **Same Performance**: Single LLM call, streaming works
4. **Simpler Code**: No ORDER_UPDATE detection logic
5. **Better Reliability**: Structured data, not string parsing

---

## Testing

To see it in action:

```bash
# Watch for function calls
tail -f /tmp/voice_agent.log | grep "Function Call"

# You should see:
[Function Call] update_order
[Order] Action: add, Items: 1
[Order] Added: 麻婆豆腐 x1 - $18
```

And in the browser console:
```javascript
[TTS] Received chunk 1 (url)  // ← Audio for "好的，我帮您点一份麻婆豆腐。"
[Order] Updated: 1 items      // ← Order UI updated
```

No "ORDER_UPDATE" anywhere in the audio or logs!
