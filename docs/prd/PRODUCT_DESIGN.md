# CamareraI Product Design

> Voice-based AI restaurant ordering assistant

**Last Updated:** 2026-02-02

---

## Design Principles

### Core Philosophy
- **Natural conversation** - Like talking to a real person, not a machine
- **Minimal friction** - No buttons, no menus to navigate, just speak
- **Elegant simplicity** - High-end restaurant tablet aesthetic

---

## User Interface

### Visual Style
- **Minimal/elegant** - Like a high-end restaurant tablet
- Clean typography, generous whitespace
- Muted color palette with subtle accents
- No chat bubbles or conversation history on screen

### Primary Focus
- **Current order summary** - Always visible, updated in real-time
- Order items with quantities and prices
- Running total
- Simple status indicator (listening/thinking/speaking)

### What NOT to Show
- Conversation history (log only for debugging)
- Transcription text on screen
- Complex controls or settings
- Gradio-style chat interface

---

## Voice Interaction

### Listening Mode
- **Always-listening** - No push-to-talk button
- Continuous voice activity detection
- Natural conversation flow

### AI Response Behavior
- **Auto-respond** - AI speaks automatically when it recognizes customer has finished a sentence
- No confirmation buttons or "send" actions
- Seamless turn-taking like human conversation

### Barge-in (Interruption)
- **Supported** - If customer interrupts while AI is speaking, stop immediately
- AI should gracefully handle interruption
- Resume listening for new input

### Audio Feedback
- **None** - No chimes, beeps, or confirmation sounds
- Pure voice interaction like talking to a real server

---

## Conversation Context

### Session Management
- AI maintains full context of current session
- Remembers:
  - Items already ordered
  - Dietary restrictions mentioned
  - Party size
  - Previous questions/preferences
- Context persists until session ends (table closes out)

### LLM Processing
- Full conversation history sent to LLM
- System prompt includes current order state
- Natural language understanding for modifications ("actually, make that two", "remove the soup")

---

## Order Management

### Order Display
- Real-time updates as items are recognized
- Clear item names with prices
- Quantity indicators
- Subtotal, tax, total

### Order Modifications
- Add items naturally ("I'll have the kung pao chicken")
- Remove items ("actually, cancel the soup")
- Modify quantities ("make that two orders")
- Special requests ("no peanuts please")

---

## Technical Requirements

### Voice Recognition
- Streaming ASR for real-time transcription
- Sentence-end detection for auto-response trigger
- Support for multiple languages (English, Mandarin, Cantonese)

### Text-to-Speech
- Natural-sounding voice
- Interruptible playback
- Consistent voice persona per table

### Latency Targets
- Voice recognition: Real-time streaming
- AI response: < 2 seconds after sentence end
- TTS playback: Start within 500ms of response

---

## Demo Priorities

For restaurant owner demos, emphasize:
1. **Natural conversation flow** - No awkward pauses or robotic responses
2. **Accurate order building** - Items correctly recognized and tallied
3. **Elegant presentation** - Professional, high-end appearance
4. **Interruption handling** - Responsive to customer needs

---

## Interaction Patterns

### Core Interaction Philosophy
- **Voice is primary**: 100% of interaction through conversation
- **Screen is supportive**: Shows order status only, no conversation display
- **Always listening**: No wake word, no push-to-talk
- **Natural turn-taking**: AI responds when customer finishes speaking

### Conversation Flow

**Basic Order Flow:**
```
[ALWAYS LISTENING]
Customer: "Hi, we'd like to order"

[AI RESPONDS - auto-triggered on sentence end]
AI: "Welcome! What can I get for you today?"

[LISTENING]
Customer: "What do you recommend for four people?"

[AI RESPONDS]
AI: "For four, I'd suggest our Kung Pao Chicken - it's our signature dish..."

[LISTENING]
Customer: "Sounds good, we'll take that"
[Order summary updates on screen]

AI: "Great! One Kung Pao Chicken. Anything else?"
```

**Interruption Flow:**
```
[AI SPEAKING]
AI: "For four people, I'd suggest our Kung Pao Chicken which is made with—"

[CUSTOMER INTERRUPTS]
Customer: "Actually we already know what we want"

[AI STOPS IMMEDIATELY, LISTENS]

Customer: "Two Mapo Tofu and one Dan Dan Noodles"

[AI RESPONDS]
AI: "Got it! Two Mapo Tofu and one Dan Dan Noodles."
[Order summary updates]
```

**Modification Flow:**
```
Customer: "Actually, make that three Mapo Tofu"

AI: "Updated to three Mapo Tofu."
[Order summary updates: 2 → 3]

Customer: "And cancel the noodles"

AI: "Removed the Dan Dan Noodles."
[Order summary updates: item removed]
```

### Screen States

**State 1: Listening (Default)**
```
┌─────────────────────────────────────┐
│                                     │
│         [Subtle pulse animation]    │
│                                     │
│              ◉ Listening            │
│                                     │
├─────────────────────────────────────┤
│  📋 Your Order                      │
│  ─────────────────────────────────  │
│  (No items yet)                     │
│                                     │
│  Total: $0.00                       │
└─────────────────────────────────────┘
```

**State 2: AI Speaking**
```
┌─────────────────────────────────────┐
│                                     │
│         [Speaking animation]        │
│                                     │
│              🗣️ Speaking            │
│         (interrupt anytime)         │
│                                     │
├─────────────────────────────────────┤
│  📋 Your Order                      │
│  ─────────────────────────────────  │
│  1x Kung Pao Chicken       $14.99   │
│  2x Mapo Tofu              $25.98   │
│  ─────────────────────────────────  │
│  Subtotal: $40.97                   │
│  Tax: $3.28                         │
│  Total: $44.25                      │
└─────────────────────────────────────┘
```

**State 3: Processing**
```
┌─────────────────────────────────────┐
│                                     │
│         [Thinking animation]        │
│                                     │
│              ⋯ Thinking             │
│                                     │
├─────────────────────────────────────┤
│  📋 Your Order                      │
│  ...                                │
└─────────────────────────────────────┘
```

### What's NOT on Screen
- No conversation history / chat bubbles
- No transcription of what customer said
- No transcription of what AI said
- No "send" or "confirm" buttons
- No settings or controls
- No wake word instructions

### Error Handling

**Didn't understand:**
```
AI: "Sorry, I didn't catch that. Could you say that again?"
[Continues listening]
```

**Noisy environment:**
```
AI: "It's a bit noisy - could you speak up a little?"
[Continues listening]
```

**Ambiguous request:**
```
Customer: "I want the chicken"
AI: "We have Kung Pao Chicken and Sweet & Sour Chicken - which would you like?"
[Continues listening]
```

---

## Future Considerations (Not for POC)

- Multi-speaker identification
- Voice cloning for brand consistency
- Kitchen display integration
- Payment processing
- Analytics dashboard
- Wake word activation (for privacy in some contexts)
- Staff/owner mode with different UI

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02-02 | Initial design decisions documented |
| 2026-02-02 | Merged interaction patterns into product design |
