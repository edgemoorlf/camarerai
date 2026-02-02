# CamareraI - Implementation Plan

**Last Updated:** 2026-02-02

---

## Tech Stack

### Backend
- **Python 3.12+** with Flask + Flask-SocketIO
- **DashScope API** - ASR (Paraformer), LLM (Qwen), TTS (Sambert)
- **WebSocket** - Real-time streaming audio

### Frontend
- **Vanilla HTML/CSS/JS** - No framework needed for POC
- **Socket.IO Client** - Real-time communication
- **Web Audio API** - Microphone capture

---

## Current Architecture

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│                 │ ◄────────────────► │                 │
│    Browser      │    Audio Stream    │  Flask Server   │
│   (Frontend)    │ ◄────────────────► │   (Backend)     │
│                 │   Transcription    │                 │
└─────────────────┘                    └────────┬────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │   DashScope     │
                                       │  ASR/LLM/TTS    │
                                       └─────────────────┘
```

---

## Implementation Phases

### Phase 1: Core Infrastructure ✅ COMPLETE
- [x] DashScope API client wrapper
- [x] Flask server with WebSocket support
- [x] Streaming ASR integration
- [x] Session management
- [x] Basic frontend with push-to-talk

### Phase 2: UI Redesign 🔄 IN PROGRESS
**Goal:** Minimal/elegant interface focused on order summary

**Tasks:**
- [ ] Remove chat interface from frontend
- [ ] Create minimal status indicator (listening/speaking/thinking)
- [ ] Design elegant order summary display
- [ ] Add subtle animations for state changes
- [ ] Implement high-end restaurant tablet aesthetic

**Files to modify:**
- `templates/index.html` - Complete redesign
- `static/style.css` - New minimal styling
- `static/app.js` - Remove chat display logic

### Phase 3: Always-Listening Mode 🔄 IN PROGRESS
**Goal:** Continuous listening without push-to-talk

**Tasks:**
- [ ] Remove push-to-talk button
- [ ] Implement continuous audio streaming
- [ ] Add voice activity detection (VAD)
- [ ] Auto-trigger AI response on sentence end
- [ ] Handle silence/pause detection

**Files to modify:**
- `static/app.js` - Auto-start recording, remove button logic
- `voice_agent.py` - Handle continuous stream, sentence detection

### Phase 4: Barge-in Support 🔄 IN PROGRESS
**Goal:** Allow customer to interrupt AI speech

**Tasks:**
- [ ] Detect voice input while TTS is playing
- [ ] Stop TTS playback immediately on interruption
- [ ] Resume listening mode
- [ ] Handle partial AI responses gracefully

**Files to modify:**
- `static/app.js` - Monitor mic during playback, stop audio
- `voice_agent.py` - Handle interrupted responses

### Phase 5: Context & Order Management
**Goal:** Maintain conversation context and build orders

**Tasks:**
- [ ] Parse order items from transcription
- [ ] Update order state in real-time
- [ ] Send full context to LLM
- [ ] Handle modifications (add/remove/change quantity)
- [ ] Display order updates on screen

**Files to modify:**
- `voice_agent.py` - Order parsing, context management
- `static/app.js` - Order display updates

### Phase 6: Polish & Demo
**Goal:** Demo-ready experience

**Tasks:**
- [ ] Fine-tune response latency
- [ ] Improve sentence-end detection
- [ ] Test various conversation scenarios
- [ ] Handle edge cases gracefully
- [ ] Create demo script

---

## File Structure

```
camarerai/
├── voice_agent.py           # Main Flask + WebSocket server
├── dashscope_client.py      # DashScope API wrapper
├── data/
│   ├── menu.json            # Restaurant menu
│   ├── knowledge.json       # Beyond-menu knowledge
│   ├── table_names.json     # Table name assignments
│   └── voices.json          # Voice configuration
├── static/
│   ├── app.js               # Frontend logic
│   └── style.css            # Styling (to be redesigned)
├── templates/
│   └── index.html           # Main UI (to be redesigned)
├── requirements.txt
├── .env                     # API keys
├── docs/
│   ├── PLAN.md                        # Overall project plan
│   ├── eng/
│   │   ├── IMPLEMENTATION_PLAN.md     # This file
│   │   └── IMPLEMENTATION_STATUS.md   # Current status
│   └── prd/
│       └── PRODUCT_DESIGN.md          # Product decisions
```

---

## Key Technical Decisions

### Always-Listening Implementation
- Use Web Audio API with continuous MediaStream
- Stream audio chunks via WebSocket
- Server-side VAD using DashScope's sentence detection
- `max_sentence_silence` parameter controls pause detection

### Barge-in Implementation
- Keep microphone active during TTS playback
- Monitor audio levels client-side
- On voice detection: stop audio, emit interrupt event
- Server cancels any pending TTS

### Order Parsing
- LLM extracts order items from conversation
- Structured output format for order updates
- Maintain order state server-side
- Push updates to client via WebSocket

---

## API Endpoints

### WebSocket Events

**Client → Server:**
- `create_session` - Initialize new session
- `start_recognition` - Begin ASR (deprecated with always-listening)
- `audio_data` - Stream audio chunks
- `stop_recognition` - End ASR (deprecated)
- `chat` - Send message to LLM
- `synthesize` - Request TTS
- `interrupt` - Stop current TTS

**Server → Client:**
- `session_created` - Session initialized
- `recognition_started` - ASR active
- `transcription_partial` - Streaming transcription
- `transcription_complete` - Final transcription
- `chat_response` - LLM response
- `synthesis_complete` - TTS audio ready
- `order_updated` - Order state changed

### REST Endpoints
- `GET /` - Serve main UI
- `GET /api/menu` - Get menu data
- `GET /api/session/<id>` - Get session details

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| ASR Latency | Real-time | ✅ Streaming |
| Sentence Detection | < 500ms | ~500ms |
| LLM Response | < 2s | ~1-2s |
| TTS Start | < 500ms | ~500ms |
| Total Round Trip | < 3s | ~3-4s |

---

## Dependencies

```
dashscope>=1.14.0
flask>=2.0.0
flask-socketio>=5.0.0
python-dotenv>=1.0.0
python-engineio>=4.0.0
python-socketio>=5.0.0
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-29 | Initial plan with DashScope integration |
| 2026-01-31 | Streaming ASR implementation |
| 2026-02-02 | Updated for UI redesign and always-listening mode |
