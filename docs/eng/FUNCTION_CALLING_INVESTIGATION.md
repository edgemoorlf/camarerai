# Function Calling Investigation - DashScope & Gemini

**Date**: 2026-02-11
**Status**: ✅ Both platforms support function calling

---

## Executive Summary

Both **DashScope (Qwen)** and **Gemini** support function calling / structured output. This is the cleanest solution for separating conversational responses from structured order data.

### Key Finding
⚠️ **Important**: Both platforms return **ONLY** the function call (structured data), **NOT** conversational text alongside it.

This means we need **two separate LLM calls**:
1. **Call 1**: With function calling → Get structured order data
2. **Call 2**: Without function calling → Get conversational response

---

## How Function Calling Works

### Concept
Instead of the LLM returning text like:
```
好的，我帮您点一份麻婆豆腐。ORDER_UPDATE: {"action": "add", "items": [...]}
```

The LLM returns structured data:
```json
{
  "function_name": "update_order",
  "arguments": {
    "action": "add",
    "items": [
      {"name": "麻婆豆腐", "quantity": 1, "price": 18}
    ]
  }
}
```

### Benefits
- ✅ **Clean separation**: No ORDER_UPDATE in text stream
- ✅ **Type safety**: Structured JSON, not string parsing
- ✅ **Validation**: Schema-based validation
- ✅ **No TTS pollution**: Structured data never goes to TTS

### Tradeoff
- ⚠️ **Two LLM calls required**: One for data, one for conversation
- ⚠️ **Increased latency**: ~800ms per call = 1.6s total
- ⚠️ **Increased cost**: 2x LLM calls

---

## DashScope (Qwen) Function Calling

### ✅ Confirmed Working

**Test Result**: Successfully returned structured order data

### API Format

```python
from dashscope import Generation

# Define function schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "update_order",
            "description": "Update the customer's food order",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "modify", "remove"],
                        "description": "The action to perform"
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "integer"},
                                "price": {"type": "number"}
                            },
                            "required": ["name", "quantity", "price"]
                        }
                    }
                },
                "required": ["action", "items"]
            }
        }
    }
]

# Call with function calling
response = Generation.call(
    api_key='your-api-key',
    model='qwen-plus',
    messages=[{"role": "user", "content": "我要一份麻婆豆腐"}],
    tools=tools,
    result_format='message'
)

# Extract function call
if response.output['choices'][0]['message']['tool_calls']:
    tool_call = response.output['choices'][0]['message']['tool_calls'][0]
    function_name = tool_call['function']['name']
    arguments = json.loads(tool_call['function']['arguments'])
```

### Response Format

```json
{
  "choices": [
    {
      "finish_reason": "tool_calls",
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "call_9a2bfb13cda3401c98b41a",
            "type": "function",
            "function": {
              "name": "update_order",
              "arguments": "{\"action\": \"add\", \"items\": [{\"name\": \"麻婆豆腐\", \"price\": 18, \"quantity\": 1}]}"
            }
          }
        ]
      }
    }
  ]
}
```

**Note**: `content` is empty - no conversational text returned.

---

## Gemini Function Calling

### ✅ Confirmed Working

**Test Result**: Successfully returned structured order data

### API Format

```python
import google.generativeai as genai
from google.ai.generativelanguage import FunctionDeclaration, Schema, Type

# Define function schema
order_update_function = FunctionDeclaration(
    name="update_order",
    description="Update the customer's food order",
    parameters=Schema(
        type=Type.OBJECT,
        properties={
            "action": Schema(
                type=Type.STRING,
                description="The action to perform",
                enum=["add", "modify", "remove"]
            ),
            "items": Schema(
                type=Type.ARRAY,
                items=Schema(
                    type=Type.OBJECT,
                    properties={
                        "name": Schema(type=Type.STRING),
                        "quantity": Schema(type=Type.INTEGER),
                        "price": Schema(type=Type.NUMBER)
                    },
                    required=["name", "quantity", "price"]
                )
            )
        },
        required=["action", "items"]
    )
)

# Create model with function calling
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=[order_update_function]
)

# Call
response = model.generate_content("我要一份麻婆豆腐")

# Extract function call
for part in response.candidates[0].content.parts:
    if hasattr(part, 'function_call') and part.function_call:
        function_name = part.function_call.name
        arguments = dict(part.function_call.args)
```

### Response Format

```python
# Response contains function_call, no text
part.function_call.name = "update_order"
part.function_call.args = {
    "action": "add",
    "items": [{"name": "麻婆豆腐", "quantity": 1, "price": 18}]
}
```

**Note**: No text response returned alongside function call.

---

## Implementation Options

### Option 1: Two Sequential Calls (Recommended)

**Flow**:
1. User speaks: "我要一份麻婆豆腐"
2. **Call 1** (with function calling): Get structured order data
3. **Call 2** (streaming, no function calling): Get conversational response
4. Stream conversational response to TTS
5. Update order UI with structured data

**Pros**:
- ✅ Clean separation of concerns
- ✅ No ORDER_UPDATE in TTS
- ✅ Streaming still works for conversation
- ✅ Type-safe order data

**Cons**:
- ⚠️ Two LLM calls = 2x cost
- ⚠️ Increased latency (~1.6s total)
- ⚠️ Need to ensure consistency between calls

**Latency Breakdown**:
```
ASR:              ~500ms
LLM Call 1:       ~800ms (function calling)
LLM Call 2:       ~800ms (streaming conversation)
TTS First Audio:  ~300ms
-----------------------------------
Total:            ~2400ms (vs 1600ms current)
```

### Option 2: Single Call with Prompt Engineering

**Flow**:
1. User speaks: "我要一份麻婆豆腐"
2. **Single streaming call** with strict prompt:
   - "ALWAYS put ORDER_UPDATE at the very end"
   - "Never put ORDER_UPDATE in the middle"
3. Detect ORDER_UPDATE in stream before sending to TTS
4. Stop TTS when detected
5. Parse ORDER_UPDATE from buffer

**Pros**:
- ✅ Single LLM call = lower cost
- ✅ Faster response time
- ✅ Streaming still works

**Cons**:
- ⚠️ Relies on LLM following instructions
- ⚠️ Risk of ORDER_UPDATE going to TTS if LLM doesn't comply
- ⚠️ String parsing instead of structured data

**Current Status**: Already implemented in voice_agent.py (lines 730-850)

### Option 3: Parallel Calls

**Flow**:
1. User speaks: "我要一份麻婆豆腐"
2. **Call 1 & 2 in parallel**:
   - Call 1: Function calling for order data
   - Call 2: Streaming for conversation
3. Stream conversation to TTS immediately
4. Update order UI when function call returns

**Pros**:
- ✅ Lowest latency (parallel execution)
- ✅ Clean separation
- ✅ Streaming works

**Cons**:
- ⚠️ 2x cost (both calls run)
- ⚠️ Potential inconsistency between calls
- ⚠️ More complex error handling

---

## Recommendation

### For Production: Option 1 (Two Sequential Calls)

**Why**:
1. **Reliability**: No risk of ORDER_UPDATE in TTS
2. **Type Safety**: Structured JSON validation
3. **Maintainability**: Clear separation of concerns
4. **Cost**: Acceptable for production use

**Implementation**:
```python
# Step 1: Get order data (function calling)
order_response = dashscope_client.chat(
    messages=messages,
    model='qwen-plus',
    tools=[order_update_tool],
    stream=False
)
order_data = extract_tool_call(order_response)

# Step 2: Get conversational response (streaming)
conversation_response = dashscope_client.chat(
    messages=messages,
    model='qwen-turbo',
    stream=True
)
# Stream to TTS sentence-by-sentence
```

### For POC/Testing: Option 2 (Current Implementation)

**Why**:
1. **Already implemented**: Working in voice_agent.py
2. **Lower cost**: Single LLM call
3. **Faster**: No additional latency
4. **Good enough**: With proper prompting

**Keep as fallback** if function calling proves too expensive.

---

## Next Steps

1. **Decide on approach**: Option 1 (two calls) vs Option 2 (current)
2. **If Option 1**: Implement two-call flow in voice_agent.py
3. **If Option 2**: Improve prompt engineering to ensure ORDER_UPDATE at end
4. **Test thoroughly**: Ensure no ORDER_UPDATE goes to TTS
5. **Monitor costs**: Track LLM API usage

---

## References

- [DashScope Function Calling Documentation](https://www.alibabacloud.com/help/en/model-studio/qwen-function-calling)
- [Gemini Function Calling Documentation](https://ai.google.dev/gemini-api/docs/function-calling)
- [Qwen Function Calling Guide](https://qwen.readthedocs.io/en/latest/framework/function_call.html)

---

## Test Results

### DashScope Test
```bash
python3 /tmp/test_dashscope_function_calling.py
```
✅ **Result**: Successfully returned structured order data
- Function name: `update_order`
- Arguments: `{"action": "add", "items": [{"name": "麻婆豆腐", "price": 18, "quantity": 1}]}`
- Content: Empty (no conversational text)

### Gemini Test
```bash
python3 /tmp/test_gemini_function_calling_v6.py
```
✅ **Result**: Successfully returned structured order data
- Function name: `update_order`
- Arguments: `{"action": "add", "items": [...]}`
- Content: Empty (no conversational text)

---

**Conclusion**: Function calling is viable and provides the cleanest separation. The tradeoff is cost vs reliability. For production, recommend Option 1 (two calls). For POC, current implementation (Option 2) is acceptable.
