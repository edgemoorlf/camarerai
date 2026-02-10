# Session Management Implementation Plan

**Feature Branch:** `feature/session-management`
**Date:** 2026-02-05
**Status:** Planning - Ready for implementation

---

## 🎯 Overview

Implement proper session management to handle the complete customer journey from ordering through payment/reset, with order persistence after confirmation.

### Key Changes

1. **Order Persistence**: Order remains visible after closing remark (not cleared)
2. **Button Evolution**: "Touch to Order" → "Tap for Anything"
3. **Order Locking**: Confirmed orders cannot be edited, only added to
4. **Session Lifecycle**: Session persists until payment or manual reset

---

## 📋 Requirements

### 1. Session Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ IDLE                                                        │
│ - No active session                                         │
│ - Button: "Touch to Order"                                  │
│ - Order panel: Hidden                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓ Tap button
┌─────────────────────────────────────────────────────────────┐
│ ENROLLING                                                   │
│ - Speaker enrollment (2.5s)                                 │
│ - Prompt: "Please say: Hello, I'd like to order"           │
│ - Button: Hidden                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓ Enrollment complete
┌─────────────────────────────────────────────────────────────┐
│ ORDERING                                                    │
│ - Customer builds order                                     │
│ - Order is EDITABLE (can modify quantities, remove items)  │
│ - Status: "Listening"                                       │
│ - Button: Hidden                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓ Say closing remark ("Thank you")
┌─────────────────────────────────────────────────────────────┐
│ CONFIRMED (Passive Listening)                               │
│ - Order is LOCKED (not editable)                            │
│ - Status: "Listening" (passive mode)                        │
│ - Button: "Tap for Anything" (visible)                      │
│ - Stop button: "Stop Listening" (visible)                   │
│ - Microphone: ACTIVE but NOT responding                     │
│ - Speech captured and stored in context                     │
│ - AI does NOT respond unless "Tap for Anything" pressed     │
│ - Order persists on screen                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓ Tap "Stop Listening"
┌─────────────────────────────────────────────────────────────┐
│ CONFIRMED (Stopped)                                         │
│ - Order is LOCKED (not editable)                            │
│ - Status: Hidden                                            │
│ - Button: "Tap for Anything" (visible)                      │
│ - Stop button: Hidden                                       │
│ - Microphone: INACTIVE                                      │
│ - Order persists on screen                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓ Tap "Tap for Anything"
┌─────────────────────────────────────────────────────────────┐
│ CONFIRMED (Active Conversation)                             │
│ - Order is LOCKED (not editable)                            │
│ - Status: "Listening" (active mode)                         │
│ - Button: Hidden                                            │
│ - Stop button: Hidden                                       │
│ - Microphone: ACTIVE and responding                         │
│ - Customer can:                                             │
│   • Add MORE items (new orders append to existing)          │
│   • Ask questions                                           │
│   • Request service                                         │
│ - Previously captured speech available as context           │
└─────────────────────────────────────────────────────────────┘
                          ↓ Payment OR Manual Reset
┌─────────────────────────────────────────────────────────────┐
│ IDLE                                                        │
│ - Session cleared                                           │
│ - Order cleared                                             │
│ - Ready for next customer                                   │
└─────────────────────────────────────────────────────────────┘
```

### 2. Session End Conditions

Session ends when:
- ✅ Successful payment (future implementation)
- ✅ Manual reset by staff

### 3. Post-Confirmation Behavior

After customer says closing remark ("Thank you"):
- ✅ Order is LOCKED (cannot modify or remove items)
- ✅ Button changes to "Tap for Anything"
- ✅ Order remains visible on screen
- 🆕 **Passive Listening Mode activated:**
  - Microphone continues capturing audio
  - Speech is transcribed and stored in conversation context
  - AI does NOT respond to captured speech
  - Customer sees "Listening" status indicator
  - "Stop Listening" button appears
- 🆕 **Customer can stop passive listening:**
  - Tap "Stop Listening" button
  - Microphone stops
  - Status indicator hidden
  - Only "Tap for Anything" button visible
- 🆕 **Customer can resume active conversation:**
  - Tap "Tap for Anything" button
  - Microphone activates in active mode
  - AI responds to speech
  - Previously captured context available
  - Customer can add items, ask questions, request service

### 4. Order Editability Rules

**During ORDERING state:**
- ✅ Can add new items
- ✅ Can modify quantities
- ✅ Can remove items

**During CONFIRMED state:**
- ✅ Can ONLY add new items
- ❌ Cannot modify existing items
- ❌ Cannot remove existing items
- ✅ LLM politely refuses modify/remove requests

### 5. Passive Listening Mode (NEW)

**Purpose:** Capture customer conversation context without interrupting their meal.

**Behavior:**
- 🆕 Activated automatically after closing remark
- 🆕 Microphone remains active
- 🆕 Speech is transcribed in real-time
- 🆕 Transcriptions stored in conversation history
- 🆕 AI does NOT generate responses
- 🆕 Customer sees "Listening" indicator (passive mode)
- 🆕 "Stop Listening" button visible

**Use Cases:**
- Customer discusses food with companions
- Customer mentions preferences or feedback
- Customer talks about dietary needs
- Context captured for future interactions

**Stop Listening:**
- Customer taps "Stop Listening" button
- Microphone deactivates
- Status indicator hidden
- Conversation context preserved

**Resume Active Mode:**
- Customer taps "Tap for Anything"
- Microphone activates in active mode
- AI can now respond
- Previously captured context available

### 6. Kitchen Integration

- ⏸️ Not implemented in this phase
- Order persists on screen for staff to manually process

---

## 🔧 Technical Design

### 1. Session States

```python
class SessionState:
    IDLE = 'idle'                    # No active session
    ENROLLING = 'enrolling'          # Speaker enrollment in progress
    ORDERING = 'ordering'            # Building order (editable)
    CONFIRMED = 'confirmed'          # Order locked (add-only)
    CONFIRMED_PASSIVE = 'confirmed_passive'  # 🆕 Passive listening (no AI response)
    CONFIRMED_STOPPED = 'confirmed_stopped'  # 🆕 Listening stopped
```

### 2. Session Class Enhancement

```python
class Session:
    def __init__(self, session_id, table_id):
        self.session_id = session_id
        self.table_id = table_id
        self.table_name = f"Table {table_id}"
        self.state = SessionState.IDLE

        # Order management
        self.current_order = []      # Items being added (editable)
        self.confirmed_items = []    # Items locked after confirmation
        self.order_confirmed_at = None

        # Conversation
        self.conversation_history = []
        self.passive_transcripts = []  # 🆕 Transcripts captured in passive mode
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
```

### 3. Order Management Logic

**During ORDERING state:**
```python
# All items in current_order are editable
current_order = [Kung Pao Chicken x1, Dan Dan Noodles x1]
confirmed_items = []

# LLM can process: add, modify, remove
```

**After first confirmation:**
```python
# Move current_order → confirmed_items (locked)
confirmed_items = [Kung Pao Chicken x1, Dan Dan Noodles x1]
current_order = []

# LLM can ONLY process: add (no modify/remove)
```

**After adding more items:**
```python
# New items go to current_order
confirmed_items = [Kung Pao Chicken x1, Dan Dan Noodles x1]
current_order = [Spring Rolls x1]

# User says "Thank you" again
```

**After second confirmation:**
```python
# Append current_order → confirmed_items
confirmed_items = [Kung Pao Chicken x1, Dan Dan Noodles x1, Spring Rolls x1]
current_order = []
```

### 4. State Transitions

```python
# IDLE → ENROLLING
# Triggered by: User taps "Touch to Order"
session.state = SessionState.ENROLLING

# ENROLLING → ORDERING
# Triggered by: Enrollment completes successfully
session.state = SessionState.ORDERING

# ORDERING → CONFIRMED_PASSIVE
# Triggered by: Closing remark detected
session.confirmed_items.extend(session.current_order)
session.current_order = []
session.state = SessionState.CONFIRMED_PASSIVE  # 🆕 Start in passive mode
session.order_confirmed_at = datetime.now()

# CONFIRMED_PASSIVE → CONFIRMED_STOPPED
# Triggered by: User taps "Stop Listening"
session.state = SessionState.CONFIRMED_STOPPED

# CONFIRMED_STOPPED → CONFIRMED (active)
# Triggered by: User taps "Tap for Anything"
session.state = SessionState.CONFIRMED

# CONFIRMED_PASSIVE → CONFIRMED (active)
# Triggered by: User taps "Tap for Anything" (without stopping first)
session.state = SessionState.CONFIRMED

# CONFIRMED → CONFIRMED_PASSIVE
# Triggered by: Closing remark detected (after adding more items)
session.confirmed_items.extend(session.current_order)
session.current_order = []
session.state = SessionState.CONFIRMED_PASSIVE

# CONFIRMED_PASSIVE/CONFIRMED_STOPPED → IDLE
# Triggered by: Payment or manual reset
session.confirmed_items = []
session.current_order = []
session.passive_transcripts = []
session.state = SessionState.IDLE
```

### 5. LLM Prompt Changes

**System prompt based on state:**

```python
if session.state == SessionState.ORDERING:
    order_rules = """
You can help customer:
- Add new items
- Modify quantities (e.g., "make that two")
- Remove items (e.g., "cancel the soup")

Use ORDER_UPDATE with actions: add, modify, remove
"""

elif session.state == SessionState.CONFIRMED:
    # 🆕 Include passive transcripts as context
    passive_context = ""
    if session.passive_transcripts:
        passive_context = f"""
Context from customer conversation:
{chr(10).join(session.passive_transcripts)}

Use this context to better understand customer preferences and needs.
"""

    order_rules = f"""
The order has been confirmed. Customer can:
- Add MORE items (new orders)
- Ask questions
- Request service

Customer CANNOT modify or remove confirmed items.

If customer tries to modify/remove, politely explain:
"Your order has been confirmed. I can add more items, but cannot modify the confirmed order. Would you like to add something else?"

Use ORDER_UPDATE ONLY with action: add
DO NOT use actions: modify, remove

{passive_context}
"""

elif session.state == SessionState.CONFIRMED_PASSIVE:
    # 🆕 Passive mode - capture but don't respond
    # This state should NOT trigger LLM generation
    pass
```

### 6. Closing Remark Handling

**Current behavior:** Resets session
**New behavior:** Transitions to CONFIRMED_PASSIVE state

```python
def handle_chat(data):
    # ... existing code ...

    # Check for closing remark
    if is_closing_remark(user_message):
        if session.state == SessionState.ORDERING:
            # First confirmation - lock order and enter passive mode
            session.confirmed_items.extend(session.current_order)
            session.current_order = []
            session.state = SessionState.CONFIRMED_PASSIVE  # 🆕 Passive mode
            session.order_confirmed_at = datetime.now()

            emit('state_changed', {
                'session_id': session_id,
                'state': 'confirmed_passive',
                'confirmed_items': session.confirmed_items,
                'button_text': 'Tap for Anything',
                'show_stop_button': True  # 🆕 Show stop listening button
            })

        elif session.state == SessionState.CONFIRMED:
            # Additional confirmation - lock new items and return to passive
            session.confirmed_items.extend(session.current_order)
            session.current_order = []
            session.state = SessionState.CONFIRMED_PASSIVE  # 🆕 Back to passive

            emit('order_updated', {
                'session_id': session_id,
                'confirmed_items': session.confirmed_items,
                'current_order': []
            })

            emit('state_changed', {
                'session_id': session_id,
                'state': 'confirmed_passive',
                'show_stop_button': True
            })

# 🆕 Handle transcription in passive mode
def handle_transcription_complete(data):
    session_id = data.get('session_id')
    text = data.get('text')

    if session_id in sessions:
        session = sessions[session_id]

        if session.state == SessionState.CONFIRMED_PASSIVE:
            # Store transcript but don't respond
            session.passive_transcripts.append(text)
            session.conversation_history.append({
                'role': 'user',
                'content': text,
                'passive': True  # Mark as passive capture
            })

            print(f"[Passive] Captured: {text}")
            # Do NOT call LLM or emit chat_response
            return

        # Normal active mode - process as usual
        # ... existing code ...
```

---

## 📁 Files to Modify

### Backend Changes

#### 1. voice_agent.py

**Add SessionState enum:**
```python
class SessionState:
    IDLE = 'idle'
    ENROLLING = 'enrolling'
    ORDERING = 'ordering'
    CONFIRMED = 'confirmed'
```

**Enhance Session class:**
```python
class Session:
    def __init__(self, session_id, table_id):
        # ... existing fields ...
        self.state = SessionState.IDLE
        self.confirmed_items = []
        self.order_confirmed_at = None
```

**Modify closing remark handling:**
- Don't reset session
- Transition to CONFIRMED state
- Lock current order

**Add state-aware LLM prompts:**
- Different prompts for ORDERING vs CONFIRMED
- Prevent modify/remove in CONFIRMED state

**Add manual reset endpoint:**
```python
@socketio.on('reset_session')
def handle_reset_session(data):
    """Manual session reset (staff action)"""
    session_id = data.get('session_id')

    if session_id in sessions:
        del sessions[session_id]

        emit('session_reset', {
            'session_id': session_id,
            'message': 'Session reset successfully'
        })

# 🆕 Add stop listening endpoint
@socketio.on('stop_listening')
def handle_stop_listening(data):
    """Stop passive listening mode"""
    session_id = data.get('session_id')

    if session_id in sessions:
        session = sessions[session_id]

        if session.state == SessionState.CONFIRMED_PASSIVE:
            session.state = SessionState.CONFIRMED_STOPPED

            emit('state_changed', {
                'session_id': session_id,
                'state': 'confirmed_stopped',
                'show_stop_button': False
            })

            print(f"[Session] Passive listening stopped for {session_id}")

# 🆕 Add resume conversation endpoint
@socketio.on('resume_conversation')
def handle_resume_conversation(data):
    """Resume active conversation from passive/stopped state"""
    session_id = data.get('session_id')

    if session_id in sessions:
        session = sessions[session_id]

        if session.state in [SessionState.CONFIRMED_PASSIVE, SessionState.CONFIRMED_STOPPED]:
            session.state = SessionState.CONFIRMED

            emit('state_changed', {
                'session_id': session_id,
                'state': 'confirmed',
                'show_stop_button': False
            })

            # Include passive context in system prompt
            print(f"[Session] Resumed active conversation for {session_id}")
            print(f"[Session] Passive context: {len(session.passive_transcripts)} transcripts")
```

**Prevent modify/remove in CONFIRMED state:**
```python
if session.state == SessionState.CONFIRMED:
    if order_update['action'] in ['modify', 'remove']:
        # Reject the action
        print(f"[Order] Rejected {order_update['action']} in CONFIRMED state")
        # Don't process the order update
        return
```

### Frontend Changes

#### 2. static/app.js

**Add state management:**
```javascript
constructor() {
    // ... existing fields ...
    this.sessionState = 'idle';
}
```

**Update button text based on state:**
```javascript
updateButton(state) {
    const button = document.getElementById('start-button');

    switch(state) {
        case 'idle':
            button.textContent = 'Touch to Order';
            button.classList.remove('hidden');
            break;

        case 'enrolling':
        case 'ordering':
            button.classList.add('hidden');
            break;

        case 'confirmed':
            button.textContent = 'Tap for Anything';
            button.classList.remove('hidden');
            break;
    }
}
```

**Handle "Tap for Anything" button:**
```javascript
handleStartOrder() {
    if (this.sessionState === 'confirmed_passive' || this.sessionState === 'confirmed_stopped') {
        // 🆕 Resume active conversation
        console.log('[Session] Resuming active conversation from passive/stopped state');

        // Emit resume event
        this.socket.emit('resume_conversation', {
            session_id: this.sessionId
        });

        // Hide button, show status
        document.getElementById('start-button').classList.add('hidden');
        document.getElementById('stop-button').classList.add('hidden');
        this.updateStatus('listening', '◉', 'Listening');

    } else if (this.sessionState === 'confirmed') {
        // Resume conversation, allow adding more items
        this.updateStatus('listening', '◉', 'Listening');
        document.getElementById('start-button').classList.add('hidden');
    } else {
        // Normal enrollment flow
        // ... existing code ...
    }
}

// 🆕 Handle stop listening button
handleStopListening() {
    console.log('[Session] Stopping passive listening');

    // Emit stop event
    this.socket.emit('stop_listening', {
        session_id: this.sessionId
    });

    // Hide status and stop button
    const statusArea = document.getElementById('status-area');
    statusArea.classList.add('hidden');

    const stopButton = document.getElementById('stop-button');
    stopButton.classList.add('hidden');

    // Show "Tap for Anything" button
    const startButton = document.getElementById('start-button');
    startButton.classList.remove('hidden');
}
```

**Display confirmed vs new items separately:**
```javascript
socket.on('order_updated', (data) => {
    this.displayOrder(data.confirmed_items, data.current_order);
});

displayOrder(confirmedItems, currentItems) {
    // Show confirmed items (locked)
    // Show current items (new)
    // Calculate totals
}
```

**Handle state changes:**
```javascript
socket.on('state_changed', (data) => {
    this.sessionState = data.state;
    this.updateButton(data.state);

    if (data.state === 'confirmed') {
        // Update UI to show order is confirmed
        this.showOrderConfirmed();
    }
});
```

**Add manual reset:**
```javascript
resetSession() {
    this.socket.emit('reset_session', {
        session_id: this.sessionId
    });
}

socket.on('session_reset', (data) => {
    // Clear UI
    // Reset to IDLE state
    this.sessionState = 'idle';
    this.updateButton('idle');
    this.clearOrder();
});
```

#### 3. templates/index.html

**Update button (dynamic text):**
```html
<button id="start-button" class="start-button">Touch to Order</button>
```

**Add sections for confirmed vs new items:**
```html
<div id="order-panel" class="order-panel hidden">
    <h2>Your Order</h2>

    <!-- Confirmed items (locked) -->
    <div id="confirmed-section" class="order-section confirmed hidden">
        <h3>Confirmed Order <span class="lock-icon">🔒</span></h3>
        <div id="confirmed-items" class="order-items locked"></div>
    </div>

    <!-- New items (being added) -->
    <div id="new-section" class="order-section new hidden">
        <h3>Additional Items</h3>
        <div id="new-items" class="order-items"></div>
    </div>

    <!-- Totals -->
    <div class="order-totals">
        <div class="total-row">
            <span>Subtotal:</span>
            <span id="subtotal">$0.00</span>
        </div>
        <div class="total-row">
            <span>Tax (9%):</span>
            <span id="tax">$0.00</span>
        </div>
        <div class="total-row total">
            <span>Total:</span>
            <span id="total">$0.00</span>
        </div>
    </div>
</div>
```

**Add manual reset button (for staff/testing):**
```html
<button id="reset-button" class="reset-button hidden">Reset Session (Staff)</button>

<!-- 🆕 Add stop listening button -->
<button id="stop-button" class="stop-button hidden">Stop Listening</button>
```

#### 4. static/style.css

**Add styles for locked items:**
```css
.order-items.locked {
    opacity: 0.7;
    background: #f5f5f5;
    border-left: 3px solid #999;
    padding-left: 10px;
}

.order-items.locked .order-item {
    color: #666;
}

.lock-icon {
    font-size: 14px;
    margin-left: 5px;
}
```

**Add styles for confirmed vs new sections:**
```css
.order-section.confirmed {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 2px solid #ddd;
}

.order-section.new {
    margin-top: 20px;
}

.order-section h3 {
    font-size: 16px;
    color: #666;
    margin-bottom: 10px;
}
```

**Add styles for "Tap for Anything" button:**
```css
.start-button.confirmed {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.start-button.confirmed:hover {
    transform: scale(1.05);
    box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4);
}
```

**Add styles for reset button:**
```css
.reset-button {
    position: fixed;
    bottom: 20px;
    left: 20px;
    padding: 10px 20px;
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    z-index: 1000;
}

.reset-button:hover {
    background: #c82333;
}

/* 🆕 Stop listening button */
.stop-button {
    position: fixed;
    bottom: 100px;
    left: 50%;
    transform: translateX(-50%);
    padding: 12px 32px;
    background: #ff9500;
    color: white;
    border: none;
    border-radius: 50px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    z-index: 100;
    box-shadow: 0 4px 16px rgba(255, 149, 0, 0.3);
    transition: all 0.2s ease;
}

.stop-button:hover {
    background: #ff8800;
    transform: translateX(-50%) translateY(-2px);
    box-shadow: 0 6px 20px rgba(255, 149, 0, 0.4);
}
```

---

## 🧪 Testing Plan

### Test Case 1: Basic Session Flow

**Steps:**
1. Tap "Touch to Order"
2. Complete enrollment
3. Order items: "Kung Pao Chicken and Dan Dan Noodles"
4. Say "Thank you"
5. Verify button changes to "Tap for Anything"
6. Verify order remains visible
7. Verify items are locked (grayed out)

**Expected:**
- ✅ Button text changes
- ✅ Order persists
- ✅ Items show as locked

### Test Case 2: Adding More Items

**Steps:**
1. Complete Test Case 1
2. Tap "Tap for Anything"
3. Order more: "Add Spring Rolls"
4. Verify new item appears separately
5. Say "Thank you" again
6. Verify all items are now locked

**Expected:**
- ✅ New items appear in separate section
- ✅ After confirmation, all items locked
- ✅ Button reappears as "Tap for Anything"

### Test Case 3: Modify Attempt (Should Fail)

**Steps:**
1. Complete Test Case 1
2. Tap "Tap for Anything"
3. Try to modify: "Change the chicken to two"
4. Verify LLM refuses politely

**Expected:**
- ✅ LLM explains order is confirmed
- ✅ LLM offers to add more items
- ✅ No modification occurs

### Test Case 4: Remove Attempt (Should Fail)

**Steps:**
1. Complete Test Case 1
2. Tap "Tap for Anything"
3. Try to remove: "Cancel the noodles"
4. Verify LLM refuses politely

**Expected:**
- ✅ LLM explains order is confirmed
- ✅ LLM offers to add more items
- ✅ No removal occurs

### Test Case 5: Manual Reset

**Steps:**
1. Complete Test Case 1
2. Click "Reset Session" button
3. Verify session clears
4. Verify button returns to "Touch to Order"
5. Verify order panel is hidden

**Expected:**
- ✅ Session cleared
- ✅ Order cleared
- ✅ UI reset to IDLE state

### Test Case 6: Multiple Confirmations

**Steps:**
1. Order items → Say "Thank you"
2. Add more items → Say "Thank you"
3. Add more items → Say "Thank you"
4. Verify all items accumulated in confirmed list

**Expected:**
- ✅ Each confirmation locks current items
- ✅ All items visible in confirmed section
- ✅ Totals calculated correctly

### Test Case 7: Questions After Confirmation
**Steps:**
1. Complete Test Case 1
2. Tap "Tap for Anything"
3. Ask: "How spicy is the Kung Pao Chicken?"
4. Verify LLM responds normally

**Expected:**
- ✅ LLM answers question
- ✅ No ORDER_UPDATE generated
- ✅ Order remains unchanged

### Test Case 8: Passive Listening Mode (NEW)
**Steps:**
1. Order items: "Kung Pao Chicken and Dan Dan Noodles"
2. Say "Thank you"
3. Verify button changes to "Tap for Anything"
4. Verify "Stop Listening" button appears
5. Verify status shows "Listening"
6. Say something: "This looks delicious"
7. Verify AI does NOT respond
8. Verify transcript captured

**Expected:**
- ✅ Passive mode activated after closing remark
- ✅ "Stop Listening" button visible
- ✅ Status indicator shows "Listening"
- ✅ Speech transcribed but no AI response
- ✅ Transcript stored in session context

### Test Case 9: Stop Listening (NEW)
**Steps:**
1. Complete Test Case 8
2. Tap "Stop Listening"
3. Verify status indicator hidden
4. Verify "Stop Listening" button hidden
5. Verify "Tap for Anything" button still visible
6. Say something
7. Verify no transcription occurs

**Expected:**
- ✅ Microphone stops
- ✅ Status indicator hidden
- ✅ Stop button hidden
- ✅ "Tap for Anything" button remains
- ✅ No audio capture

### Test Case 10: Resume with Passive Context (NEW)
**Steps:**
1. Complete Test Case 8 (passive mode with captured speech)
2. Tap "Tap for Anything"
3. Ask: "Can you recommend something spicy?"
4. Verify AI response uses passive context

**Expected:**
- ✅ Active conversation mode activated
- ✅ AI has access to passive transcripts
- ✅ AI response considers previous context
- ✅ Can add items, ask questions normally

### Test Case 11: Multiple Passive Captures (NEW)
**Steps:**
1. Order items → Say "Thank you" (passive mode)
2. Say: "I love spicy food"
3. Say: "This restaurant is great"
4. Tap "Tap for Anything"
5. Ask: "What else do you recommend?"
6. Verify AI uses all passive context

**Expected:**
- ✅ All passive transcripts captured
- ✅ AI considers all context when responding
- ✅ Recommendations align with captured preferences

---

## 📊 Success Criteria

After implementation, the system should:

### Session Management
- ✅ Session persists after closing remark
- ✅ Session ends only on payment or manual reset
- ✅ State transitions work correctly
- ✅ Button text reflects current state

### Order Locking
- ✅ Confirmed items cannot be modified
- ✅ Confirmed items cannot be removed
- ✅ Customer can only ADD new items after confirmation
- ✅ LLM politely refuses modify/remove requests

### Multiple Confirmations
- ✅ Customer can say "Thank you" multiple times
- ✅ Each confirmation locks current items
- ✅ All items accumulate in confirmed list
- ✅ Totals calculated correctly

### UI Clarity
- ✅ Clear visual distinction between confirmed and new items
- ✅ Lock icon or grayed out style for confirmed items
- ✅ Button text changes appropriately
- ✅ Order remains visible after confirmation

### Manual Reset
- ✅ Staff can reset session manually
- ✅ Reset clears all data
- ✅ Returns to IDLE state
- ✅ Ready for next customer

### Passive Listening (NEW)
- ✅ Passive mode activates after closing remark
- ✅ Microphone continues capturing audio
- ✅ Speech transcribed and stored in context
- ✅ AI does NOT respond in passive mode
- ✅ "Stop Listening" button visible and functional
- ✅ Customer can stop passive listening
- ✅ Passive context available when resuming conversation
- ✅ AI uses passive context for better responses

---

## 🚀 Implementation Phases

### Phase 1: Backend Session State Management
**Files:** `voice_agent.py`

Tasks:
- [ ] Add `SessionState` enum with CONFIRMED_PASSIVE and CONFIRMED_STOPPED states
- [ ] Enhance `Session` class with state field
- [ ] Add `confirmed_items` list
- [ ] Add `passive_transcripts` list for context capture
- [ ] Implement state transition logic
- [ ] Modify closing remark handling (transition to CONFIRMED_PASSIVE)
- [ ] Add state-aware LLM prompts
- [ ] 🆕 Add passive listening mode (capture but don't respond)
- [ ] 🆕 Add stop_listening endpoint
- [ ] 🆕 Add resume_conversation endpoint
- [ ] 🆕 Include passive context in LLM prompts when resuming

**Estimated effort:** 3-4 hours

### Phase 2: Order Locking Logic
**Files:** `voice_agent.py`

Tasks:
- [ ] Implement order locking on confirmation
- [ ] Prevent modify/remove in CONFIRMED state
- [ ] Allow only add actions after confirmation
- [ ] Add polite refusal messages in LLM prompt
- [ ] Test order state transitions

**Estimated effort:** 1-2 hours

### Phase 3: Frontend State Management
**Files:** `static/app.js`

Tasks:
- [ ] Add state tracking (including CONFIRMED_PASSIVE and CONFIRMED_STOPPED)
- [ ] Update button text dynamically
- [ ] Handle "Tap for Anything" button (resume from passive/stopped)
- [ ] Handle state change events (passive, stopped, active)
- [ ] Add manual reset functionality
- [ ] 🆕 Add stop listening button handler
- [ ] 🆕 Handle passive mode UI (show status + stop button)
- [ ] 🆕 Handle stopped mode UI (hide status, show only "Tap for Anything")
- [ ] 🆕 Emit stop_listening and resume_conversation events

**Estimated effort:** 3-4 hours

### Phase 4: UI Updates
**Files:** `templates/index.html`, `static/style.css`

Tasks:
- [ ] Separate confirmed vs new items display
- [ ] Add lock icon for confirmed items
- [ ] Style confirmed items (subtle indicator, not grayed out)
- [ ] Update order totals calculation
- [ ] Add manual reset button
- [ ] 🆕 Add stop listening button
- [ ] 🆕 Style stop button (floating, orange, prominent)
- [ ] 🆕 Update status indicator for passive mode
- [ ] Polish visual design

**Estimated effort:** 2-3 hours

### Phase 5: Testing & Polish
**Files:** All

Tasks:
- [ ] Test full session lifecycle
- [ ] Test multiple confirmations
- [ ] Test order locking
- [ ] Test modify/remove rejection
- [ ] Test manual reset
- [ ] 🆕 Test passive listening mode (capture without response)
- [ ] 🆕 Test stop listening functionality
- [ ] 🆕 Test resume conversation with passive context
- [ ] 🆕 Verify passive transcripts stored correctly
- [ ] 🆕 Verify AI uses passive context when resuming
- [ ] Test edge cases
- [ ] Fix bugs
- [ ] Polish UX

**Estimated effort:** 3-4 hours

**Total estimated effort:** 13-18 hours (increased from 9-14 hours due to passive listening feature)

---

## 🔄 Migration Notes

### Breaking Changes

**Session behavior:**
- Old: Session resets after closing remark
- New: Session persists, order locked

**Button text:**
- Old: Always "Touch to Order"
- New: "Touch to Order" → "Tap for Anything"

**Order editability:**
- Old: Always editable until reset
- New: Locked after confirmation

### Backward Compatibility

- ✅ Existing sessions will continue to work
- ✅ No database changes required (in-memory sessions)
- ✅ No API changes for existing endpoints
- ✅ New endpoints are additive

---

## 📝 Future Enhancements

### Payment Integration
- Add payment endpoint
- Transition CONFIRMED → IDLE on successful payment
- Send order to kitchen on payment

### Session Timeout
- Auto-reset session after X minutes of inactivity
- Warning before timeout
- Save order state before timeout

### Passive Listening Enhancements
- 🆕 Visual indicator for passive mode (different color/style)
- 🆕 Show count of captured transcripts
- 🆕 Allow customer to review captured context
- 🆕 Privacy controls (clear passive transcripts)
- 🆕 Configurable passive mode (auto-enable or manual)

### Order History
- Store completed orders in database
- View order history per table
- Analytics and reporting

### Multi-Table Management
- Staff dashboard to view all active sessions
- Bulk reset for table turnover
- Session transfer between tables

---

## 📚 References

### Related Documents
- `docs/eng/IMPLEMENTATION_PLAN.md` - Overall implementation plan
- `docs/eng/TEST_PLAN.md` - Comprehensive test plan
- `docs/prd/PRODUCT_DESIGN.md` - Product design decisions

### Related Issues
- Order persistence after closing remark
- Button text evolution
- Session lifecycle management

---

**Status:** Ready for implementation
**Next Step:** Begin Phase 1 - Backend Session State Management
**Branch:** `feature/session-management`
