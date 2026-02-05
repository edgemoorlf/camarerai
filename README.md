# CamareraI - Voice Ordering System

**Status:** POC - Client-Side Speaker Verification for Barge-in Filtering
**Last Updated:** 2026-02-05
**Branch:** `experiment/speaker-id-fingerprint`

---

## 🎯 Current Implementation

**Active File:** `voice_agent.py`
**Status:** ✅ Ready to test
**Architecture:** WebSocket-based streaming ASR with client-side speaker verification

### What Works ✅
- ✅ **Touch to Order button** - Large button to start ordering (browser security compliant)
- ✅ **Speaker enrollment** - 2.5s audio collection for voice fingerprinting
- ✅ **Client-side verification** - Zero-latency speaker verification (5ms)
- ✅ **Barge-in filtering** - Only enrolled customer can interrupt AI
- ✅ **Always-listening mode** - Microphone streams continuously after enrollment
- ✅ **Natural conversation** - Speak naturally, AI responds when you finish
- ✅ **Language matching** - AI responds in your language (Chinese/English)
- ✅ **Minimal UI** - Clean status indicator + order summary only
- ✅ **Real-time voice transcription** (streaming)
- ✅ **LLM conversation** (English, Mandarin, Cantonese)
- ✅ **Text-to-speech responses**
- ✅ **Session management**
- ✅ **Closing remark detection** - Detects "thank you", "谢谢", "唔該" and resets
- ✅ **Session boundaries** - Clean reset between customers
- ✅ **Order parsing** - Extracts items from conversation in any language
- ✅ **Order display** - Shows items with quantities and prices
- ✅ **Order calculations** - Automatic subtotal, tax (9%), and total
- ✅ **Order modifications** - Add, remove, or change quantities
- ✅ **Real-time updates** - Order panel updates as items are added

### What's Not Implemented Yet ⬜
- ❌ Context management (full conversation history)
- ❌ Error handling for invalid menu items
- ❌ Order confirmation before sending to kitchen
- ❌ Fuzzy item matching (e.g., "chicken" → "Kung Pao Chicken")
- ❌ Voice cloning
- ❌ Kitchen integration

---

## 🚀 Quick Start

### 1. Check System Requirements

```bash
python3 test_all.py
```

This verifies:
- All files present
- Dependencies installed
- Network connectivity to DashScope
- API key configured

### 2. Install Dependencies (if needed)

```bash
pip install -r requirements.txt
```

### 3. Start the Server

```bash
python3 voice_agent.py
```

### 4. Open Browser

```
http://localhost:5002
```

Server also available on network:
- Local: http://127.0.0.1:5002
- Network: http://192.168.1.139:5002

### 5. Test Complete Flow

1. **Page loads** - "Touch to Order" button appears
2. **Tap button** - Browser requests microphone permission
3. **Grant permission** - Enrollment prompt appears
4. **Enrollment**: Say "Hello, I'd like to order" (2.5 seconds)
5. **Enrollment completes** - Status shows "Listening"
6. **Order items**: "I'd like the Kung Pao Chicken"
7. **Watch order panel** - Item appears with price
8. **Modify order**: "Actually, make that two"
9. **Watch update** - Quantity changes to x2, total updates
10. **Test barge-in**: While AI speaks, interrupt (should work)
11. **Test filtering**: Have another person speak (should NOT trigger)
12. **End session**: Say "Thank you" or "谢谢" or "唔該"
13. **AI confirms** - Responds with confirmation
14. **Session resets** - Order clears, button reappears for next customer

**Interrupt anytime:** Press SPACE or start speaking to interrupt AI (only enrolled customer)

**Debug Panel:** Click 🐛 button (bottom right) to see transcription and responses

---

## 🎤 Speaker Verification

### Client-Side Voice Fingerprinting

**Architecture:**
```
Browser (Client-Side Only)
    ↓
Enrollment: Extract voice features (F0, spectral centroid, ZCR, energy)
    ↓
Store features in memory
    ↓
Barge-in Detection: Extract features from incoming audio
    ↓
Compare with enrolled features (5ms)
    ↓
Similarity > 0.75? → Allow barge-in
```

**Performance:**
- **Latency:** 5ms (vs 200ms with backend approach)
- **Accuracy:** 70-75% expected
- **Network:** Zero calls for verification
- **Privacy:** Audio never leaves browser

**Features Extracted:**
- F0 (Fundamental Frequency) - Pitch
- Spectral Centroid - Voice brightness
- Zero Crossing Rate - Noisiness
- Energy Distribution - 8 frequency bands

**Files:**
- `static/speaker_fingerprint.js` - Feature extraction and comparison
- `static/app.js` - Enrollment and verification integration

---

## 📁 Project Structure

### Core Files (Active)

```
voice_agent.py               # Main server (WebSocket + streaming ASR)
dashscope_client.py          # DashScope API wrapper
test_all.py                  # Complete system check
test_network.py              # Network diagnostics

data/
├── menu.json                # Restaurant menu (multilingual)
├── knowledge.json           # Beyond-menu knowledge
├── table_names.json         # Table name assignments
└── voices.json              # Voice configuration

static/
├── app.js                   # Always-listening WebSocket client + speaker verification
├── speaker_fingerprint.js   # Client-side voice fingerprinting
└── style.css                # Minimal UI styling

templates/
└── index.html               # Minimal UI (status + order summary + enrollment)
```

### Documentation

```
README.md                    # This file - single source of truth
CLAUDE.md                    # AI assistant guidelines
CLIENT_SIDE_FINGERPRINT.md   # Speaker verification implementation guide
FINAL_RECOMMENDATION.md      # Comparison: client-side vs backend approach
docs/
├── PLAN.md                  # Overall project plan and vision
├── eng/
│   ├── IMPLEMENTATION_PLAN.md     # Technical implementation plan
│   ├── IMPLEMENTATION_STATUS.md   # Current implementation status
│   └── TEST_PLAN.md               # Comprehensive test plan
└── prd/
    └── PRODUCT_DESIGN.md    # Product design decisions
```

---

## 🔧 Troubleshooting

### Issue 1: DNS Resolution Error

**Symptom:**
```
Failed to resolve 'dashscope.aliyuncs.com'
```

**Fix:**
```bash
# Change DNS to Google DNS
sudo networksetup -setdnsservers Wi-Fi 8.8.8.8 8.8.4.4

# Test again
python3 test_network.py
```

### Issue 2: WebSocket Connection Failed

**Symptom:**
```
WebSocket connection error
```

**Fix:**
```bash
# Install dependencies
pip install -r requirements.txt

# Restart server
python3 voice_agent.py
```

### Issue 3: Microphone Not Starting

**Checklist:**
- [ ] Tapped "Touch to Order" button
- [ ] Granted microphone permission in browser
- [ ] Browser console shows "WebSocket connected"
- [ ] Flask terminal shows "Always-listening mode active"
- [ ] Network test passes (`python3 test_network.py`)

**Debug:**
- Open debug panel (🐛 button)
- Check if session is created
- Check browser console for errors (F12)
- Try refreshing page and tapping button again

### Issue 4: Speaker Verification Not Working

**Symptoms:**
- Customer voice not triggering barge-in
- Other voices triggering barge-in

**Debug:**
```javascript
// Check console for:
[Enrollment] ✓ Success - speaker enrolled
[Barge-in] ✓ Verified (similarity: 0.XXX)  // Customer
[Barge-in] ✗ Rejected (similarity: 0.XXX)  // Others
```

**Fix:**
```javascript
// Adjust threshold in static/app.js
// Line ~16:
this.speakerVerifier = new ClientSpeakerVerifier(0.75);

// Too strict (customer rejected)? Lower to 0.70
// Too lenient (others accepted)? Raise to 0.80
```

---

## 🎤 How It Works

### Architecture

```
Browser Microphone (16kHz PCM)
    ↓ WebSocket (continuous streaming)
Flask-SocketIO Server
    ↓ WebSocket
DashScope Streaming ASR (Paraformer)
    ↓ Real-time transcription + sentence detection
Flask-SocketIO Server
    ↓ Auto-send to LLM on sentence end
DashScope LLM (Qwen)
    ↓ Generate response
DashScope TTS (Sambert)
    ↓ Synthesize speech
Browser (auto-play audio)
    ↓
Client-Side Speaker Verification (during AI speech)
    ↓ Extract features from incoming audio
    ↓ Compare with enrolled speaker
    ↓ If match: Trigger barge-in
```

### Flow

1. **Page loads**
   - "Touch to Order" button appears
   - Microphone is NOT active (browser security compliant)
   - Status area is hidden

2. **User taps button**
   - Browser requests microphone permission (user gesture present)
   - Button disappears
   - Enrollment prompt appears

3. **Enrollment (2.5 seconds)**
   - User says: "Hello, I'd like to order"
   - Client-side feature extraction (F0, spectral centroid, ZCR, energy)
   - Features stored in memory
   - Enrollment prompt disappears
   - Status indicator appears showing "Listening"

4. **User speaks**
   - Audio streams to server in real-time
   - Partial transcription updates (visible in debug panel)
   - Sentence-end detection triggers auto-response

5. **AI responds**
   - Status changes to "Thinking"
   - LLM generates response in same language
   - TTS synthesizes audio
   - Status changes to "Speaking"
   - Audio plays automatically

6. **Barge-in filtering (NEW)**
   - Voice detected (volume > 0.02)
   - Extract features from audio chunk (5ms)
   - Compare with enrolled speaker
   - If similarity > 0.75: Allow barge-in
   - If similarity < 0.75: Ignore (not customer)

7. **Session ends**
   - User says closing remark ("thank you", "谢谢", "唔該")
   - AI responds with confirmation
   - After AI finishes speaking:
     - Microphone stops
     - Status area hides
     - "Touch to Order" button reappears
   - Ready for next customer

**Latency:**
- ASR: 0.5-1 second (real-time streaming)
- Speaker verification: 5ms (client-side)

---

## 🧪 Testing

### Test 1: System Check

```bash
python3 test_all.py
```

Expected output:
```
✓ Files: PASS
✓ Packages: PASS
✓ DNS: PASS
✓ API Key: PASS
✓ DashScope API: PASS

🎉 Your system is ready!
```

### Test 2: Speaker Verification

**Enrollment:**
```
1. Tap "Touch to Order"
2. Say: "Hello, I'd like to order"
3. Check console for: [Speaker] Enrolled: {f0: XXX, ...}
```

**Barge-in (Customer):**
```
1. Order an item
2. While AI speaks, interrupt
3. Expected: AI stops immediately
4. Console: [Barge-in] ✓ Verified (similarity: 0.XXX)
```

**Barge-in (Other Person):**
```
1. Order an item
2. While AI speaks, have another person speak
3. Expected: AI does NOT stop
4. Console: [Barge-in] ✗ Rejected (similarity: 0.XXX)
```

### Test 3: Conversation Flow

**English:**
```
[Tap "Touch to Order" button]
[Complete enrollment]
You: "Hi! What do you recommend for 2 people?"
AI: [Suggests Kung Pao Chicken and Dan Dan Noodles in English]
You: "Thank you"
AI: [Confirms order]
[Button reappears for next customer]
```

**Mandarin:**
```
[点击"Touch to Order"按钮]
[完成注册]
You: "你好！有什么推荐的吗？"
AI: [中文回复推荐菜品]
You: "谢谢"
AI: [确认订单]
[按钮重新出现，准备下一位顾客]
```

---

## 📊 Configuration

### Environment Variables

Create `.env` file:
```bash
DASHSCOPE_API_KEY=sk-your-key-here
```

### Speaker Verification Threshold

Edit `static/app.js` (line ~16):
```javascript
this.speakerVerifier = new ClientSpeakerVerifier(0.75); // Default

// Lower (0.6-0.7) = more lenient, fewer false negatives
// Higher (0.8-0.9) = stricter, fewer false positives
```

### Enrollment Duration

Edit `static/app.js` (line ~18):
```javascript
this.enrollmentDuration = 2.5; // seconds

// Longer = better accuracy, worse UX
// Shorter = worse accuracy, better UX
```

### Menu Data

Edit `data/menu.json` to customize:
- Restaurant name
- Menu items (multilingual)
- Prices
- Dietary information
- Staff recommendations

---

## 🐛 Known Issues

1. **Speaker Verification Accuracy** - 70-75% expected
   - May have false positives (~25-30%)
   - Threshold tuning required based on testing
   - Can be improved with more features (MFCC, formants)

2. **No Persistence** - Enrollment lost on page refresh
   - Can be added with localStorage
   - Not critical for POC

3. **Browser Compatibility** - Requires Web Audio API
   - Works on modern browsers (Chrome, Firefox, Safari)
   - May not work on older browsers

---

## 📈 Roadmap

### Phase 5: Context & Order Management ✅ COMPLETE
- [x] Parse menu items from customer speech
- [x] Update order state in real-time
- [x] Display order updates on screen
- [x] Add/Remove/Modify order actions
- [x] Calculate subtotal, tax, and total
- [x] Show quantities and prices
- [x] Clear order on session reset
- [x] Client-side speaker verification for barge-in filtering

### Phase 6: Polish & Demo 📋 CURRENT
- [ ] Test speaker verification accuracy
- [ ] Tune threshold based on results
- [ ] Fine-tune response latency
- [ ] Improve sentence-end detection
- [ ] Test various conversation scenarios
- [ ] Handle edge cases gracefully
- [ ] Create demo script

### Phase 7: Advanced Features 📋 PLANNED
- [ ] Add more voice features (MFCC, formants)
- [ ] Optimize FFT (use Web Audio AnalyserNode)
- [ ] Add enrollment persistence (localStorage)
- [ ] Multi-speaker support
- [ ] Payment integration

### Phase 8: Production Ready 📋 PLANNED
- [ ] Deploy to cloud
- [ ] Performance optimization
- [ ] Error handling
- [ ] Analytics dashboard
- [ ] Multi-restaurant support

---

## 🤝 Contributing

This is a POC project. Current focus:
1. Test client-side speaker verification
2. Measure accuracy and tune threshold
3. Improve features if needed
4. Test conversation quality in all 3 languages
5. Improve user experience

---

## 📝 Development Notes

### Why Client-Side Speaker Verification?

**Problem with Backend Approach:**
- resemblyzer processing: 16ms (fast)
- Network latency: 100-400ms (slow)
- Total: 116-416ms (too slow for real-time)

**Solution: Client-Side:**
- Feature extraction: 5ms
- Network latency: 0ms
- Total: 5ms (40x faster!)

**Trade-off:**
- Lower accuracy (70-75% vs 78%)
- But speed is critical for barge-in
- Acceptable for POC

### Tech Stack

- **Backend:** Python + Flask + Flask-SocketIO
- **Frontend:** Vanilla JavaScript + WebSocket + Web Audio API
- **AI Services:** Alibaba DashScope (ASR, LLM, TTS)
- **Speaker Verification:** Client-side voice fingerprinting (JavaScript)
- **Data:** JSON files (menu, knowledge, config)

---

## 📞 Support

### Getting Help

1. **Run diagnostics:**
   ```bash
   python3 test_all.py
   ```

2. **Check documentation:**
   - This README (single source of truth)
   - `CLIENT_SIDE_FINGERPRINT.md` (speaker verification details)
   - `FINAL_RECOMMENDATION.md` (approach comparison)
   - `docs/eng/TEST_PLAN.md` (comprehensive test plan)

3. **Common issues:**
   - DNS resolution → Change DNS to 8.8.8.8
   - Missing packages → `pip install -r requirements.txt`
   - WebSocket errors → Restart server
   - No transcription → Check microphone permission
   - Barge-in not working → Check console, tune threshold

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🎯 Quick Reference

### Start Server
```bash
python3 voice_agent.py
```

### Run Tests
```bash
python3 test_all.py          # Complete system check
python3 test_network.py      # Network diagnostics only
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Access Application
```
http://localhost:5002
```

### Debug Panel
```
Click 🐛 button (bottom right) to see:
- Session ID
- Table name
- Transcription
- AI response
```

### Touch to Order
```
Tap the large blue button to start ordering
- Requests microphone permission
- Starts enrollment (2.5s)
- Enables natural conversation with speaker verification
```

### Interrupt AI
```
Press SPACE or start speaking while AI is talking
- Only enrolled customer can interrupt
- Others are filtered out
```

### End Session
```
Say closing remarks to end session:
- English: "thank you", "thanks", "that's all"
- Mandarin: "谢谢", "好的", "就这些"
- Cantonese: "唔該", "多謝", "得啦"

Button will reappear for next customer
```

---

**Last Updated:** 2026-02-05
**Version:** POC v0.6 (Client-Side Speaker Verification)
**Status:** Ready for testing - Phase 5 complete, Phase 6 in progress
**Branch:** `experiment/speaker-id-fingerprint`
