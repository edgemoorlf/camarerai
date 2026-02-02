# ASR Fix Summary - What You Need to Know

## The Problem

The 400 error on `/api/voice/transcribe` happens because:

**DashScope ASR API requires a publicly accessible URL to download the audio file.**

When you run locally at `http://localhost:5002`, DashScope's servers cannot reach your machine to download the audio file.

## The Solution

I've implemented **3 ways** to test the application:

### ✅ Solution 1: Text Input Fallback (EASIEST - Works Now)

**How to use:**
1. Start the app: `python3 poc_voice_agent.py`
2. Open: `http://localhost:5002`
3. **Double-click anywhere in the conversation area**
4. Type your message in the prompt dialog
5. Press OK

**This bypasses ASR entirely** and lets you test:
- ✅ LLM conversation (English, Mandarin, Cantonese)
- ✅ Menu recommendations
- ✅ Conversation history
- ✅ TTS audio responses (if working)
- ✅ Full UI functionality

### ⚙️ Solution 2: Use ngrok (For Voice Testing)

**Setup:**
```bash
# Terminal 1: Start Flask
python3 poc_voice_agent.py

# Terminal 2: Start ngrok
ngrok http 5002
```

**Then update one line in `poc_voice_agent.py`:**

Find line ~185:
```python
audio_url = f"{request.host_url}api/audio/{file_id}"
```

Replace with your ngrok URL:
```python
audio_url = "https://YOUR-NGROK-ID.ngrok.io/api/audio/{file_id}"
```

Restart the app, and voice recording will work!

### 🔄 Solution 3: Upload to OSS (Production)

For production deployment, upload audio files to Alibaba Cloud OSS and pass the OSS URL to DashScope. (Not needed for POC testing)

## What's Working Right Now

### ✅ Fully Working (No Setup Needed)
- Session management
- Text-based conversation (double-click to use)
- LLM responses in 3 languages
- Menu knowledge base
- Conversation history display
- UI and styling
- Debug panel

### ⚠️ Needs ngrok Setup
- Voice recording → transcription (ASR)

### 🎵 Should Work (May Need Testing)
- Text → speech (TTS)
- Audio playback in browser

## Quick Test Instructions

### Test 1: Verify LLM Works
```bash
python3 test_connection.py
```

Expected output:
```
✓ Client initialized successfully
✓ LLM test passed!
  Response: Hello! 你好！ 你好！
✓ TTS test passed!
  Audio URL: https://...
```

### Test 2: Test Full Conversation Flow
```bash
# Start the app
python3 poc_voice_agent.py

# Open browser to http://localhost:5002
# Double-click conversation area
# Type: "Hi! What do you recommend for 2 people?"
# See AI response
```

### Test 3: Test Multilingual
```bash
# In the app, double-click and type:
"你好！有什么推荐的吗？"

# AI should respond in Chinese
```

## Files I've Updated

1. **poc_voice_agent.py**
   - Added `/api/audio/<file_id>` endpoint to serve audio files
   - Updated TTS to use new DashScope API
   - Added better error handling

2. **static/app.js**
   - Added text input fallback (double-click feature)
   - Better error messages
   - Graceful TTS failure handling

3. **quick_test.py**
   - Fixed version check error

4. **New files:**
   - `test_connection.py` - Simple connection test
   - `test_flow.py` - Test conversation flow
   - `QUICK_START.md` - Detailed instructions
   - `TROUBLESHOOTING.md` - Common issues
   - `AUDIO_FIX.md` - Technical details

## Recommended Testing Path

**Step 1:** Test LLM connection
```bash
python3 test_connection.py
```

**Step 2:** Start the application
```bash
python3 poc_voice_agent.py
```

**Step 3:** Open browser
```
http://localhost:5002
```

**Step 4:** Test with text input
- Double-click conversation area
- Type: "Hi! What do you recommend for 2 people?"
- Verify AI responds with menu recommendations

**Step 5:** Test multilingual
- Type: "你好！有什么推荐的吗？"
- Verify AI responds in Chinese

**Step 6:** (Optional) Set up ngrok for voice testing

## Expected Behavior

### When Using Text Input:
1. Double-click conversation area
2. Prompt dialog appears
3. Type message and press OK
4. Message appears in conversation
5. Status shows "Thinking..."
6. AI response appears
7. Status shows "Speaking..." (if TTS works)
8. Audio plays (if TTS works)
9. Status returns to "Ready"

### When Using Voice (with ngrok):
1. Click "Tap to Talk" button
2. Status shows "Listening..."
3. Speak into microphone
4. Click button again to stop
5. Status shows "Transcribing..."
6. Transcription appears
7. AI responds
8. Audio plays

## Common Issues

### "Session not created"
- Refresh the page
- Check Flask terminal for errors

### "Chat failed"
- Verify DASHSCOPE_API_KEY in .env
- Check internet connection
- Look at Flask terminal output

### "Transcription failed"
- **Use text input instead** (double-click)
- Or set up ngrok

### No audio playback
- Check browser console (F12)
- Verify TTS URL is generated
- Try different browser (Chrome recommended)

## What to Test

### Core Functionality
- [ ] Application starts
- [ ] UI loads in browser
- [ ] Text input works (double-click)
- [ ] AI responds to messages
- [ ] Conversation history displays

### Conversation Quality
- [ ] AI understands questions
- [ ] AI provides relevant menu recommendations
- [ ] AI responds in correct language
- [ ] Responses are natural and helpful

### Multilingual
- [ ] English conversation works
- [ ] Mandarin conversation works
- [ ] Cantonese conversation works
- [ ] AI maintains language consistency

## Next Steps After Testing

Once text-based conversation works:

1. **Implement order parsing** - Extract menu items from conversation
2. **Add order confirmation** - Show items in order panel
3. **Set up ngrok** - Test voice input
4. **Test TTS** - Verify audio playback
5. **Polish UI** - Improve visual feedback
6. **Add more menu items** - Expand the menu
7. **Test edge cases** - Handle errors gracefully

## Summary

**The application is ready to test with text input!**

The ASR issue is a deployment/networking issue, not a code bug. The workaround (text input) lets you test everything else while we figure out the best ASR solution for your use case.

**To start testing right now:**
```bash
python3 poc_voice_agent.py
# Open http://localhost:5002
# Double-click conversation area
# Start chatting!
```
