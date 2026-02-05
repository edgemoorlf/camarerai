"""
Integration plan for speaker verification with barge-in filtering

This document outlines how to integrate resemblyzer speaker verification
into the voice agent for barge-in filtering in restaurant environment.
"""

# INTEGRATION PLAN

## Phase 1: Enrollment Flow (NEXT)

### 1.1 Add enrollment endpoint to voice_agent.py

```python
@socketio.on('enroll_speaker')
def handle_enroll_speaker(data):
    """Enroll speaker from audio sample"""
    session_id = data.get('session_id')
    audio_base64 = data.get('audio')

    if not session_id or session_id not in sessions:
        emit('error', {'message': 'Invalid session'})
        return

    session = sessions[session_id]

    # Decode audio
    audio_bytes = base64.b64decode(audio_base64)
    # Convert to float32 numpy array (16kHz, mono)
    audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    # Enroll speaker
    success, message = session.speaker_verifier.enroll_speaker(audio_array)

    emit('enrollment_result', {
        'session_id': session_id,
        'success': success,
        'message': message
    })
```

### 1.2 Modify frontend (app.js) to collect enrollment audio

```javascript
// After "Touch to Order" button tap
async handleStartOrder() {
    // Show enrollment prompt
    this.showEnrollmentPrompt();

    // Start recording for enrollment (2-3 seconds)
    await this.startEnrollmentRecording();
}

async startEnrollmentRecording() {
    // Record 2-3 seconds of audio
    // Send to server for enrollment
    // Wait for enrollment_result
    // Then start normal ordering flow
}
```

## Phase 2: Barge-in Filtering (AFTER ENROLLMENT)

### 2.1 Add verification to audio_data handler

```python
@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle streaming audio data with speaker verification"""
    try:
        if request.sid not in active_recognitions:
            return

        rec_data = active_recognitions[request.sid]
        session_id = rec_data['session_id']
        session = sessions.get(session_id)

        if not session:
            return

        # Decode audio
        audio_base64 = data.get('audio')
        audio_bytes = base64.b64decode(audio_base64)

        # Convert to float32 for verification
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Check if AI is speaking (barge-in scenario)
        is_ai_speaking = data.get('is_speaking', False)

        if is_ai_speaking and session.speaker_verifier.is_enrolled():
            # Verify speaker before allowing barge-in
            is_match, similarity = session.speaker_verifier.verify_speaker(audio_array)

            if is_match:
                # Customer speaking - allow barge-in
                emit('barge_in_verified', {
                    'session_id': session_id,
                    'similarity': similarity
                })
            else:
                # Not customer - ignore (don't trigger barge-in)
                print(f"[Barge-in] Rejected: similarity {similarity:.3f} < threshold")
                return

        # Continue with normal ASR processing
        recognition = rec_data['recognition']

        if not rec_data['started']:
            recognition.start()
            rec_data['started'] = True

        recognition.send_audio_frame(audio_bytes)

    except Exception as e:
        print(f"[ASR] Audio data error: {e}")
```

### 2.2 Modify frontend to send is_speaking flag

```javascript
processor.onaudioprocess = (e) => {
    if (!this.isRecording) return;

    const inputData = e.inputBuffer.getChannelData(0);

    // Convert to PCM
    const pcmData = new Int16Array(inputData.length);
    for (let i = 0; i < inputData.length; i++) {
        const s = Math.max(-1, Math.min(1, inputData[i]));
        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }

    // Send with is_speaking flag
    const base64Audio = this.arrayBufferToBase64(pcmData.buffer);
    this.socket.emit('audio_data', {
        audio: base64Audio,
        is_speaking: this.isSpeaking  // NEW: Tell server if AI is speaking
    });

    // Check for barge-in (only if enrolled)
    if (this.isSpeaking && this.speakerEnrolled) {
        const volume = this.calculateVolume(inputData);
        if (volume > 0.02) {
            // Voice detected - server will verify if it's customer
            // Wait for barge_in_verified event
        }
    }
};
```

### 2.3 Handle barge_in_verified event

```javascript
this.socket.on('barge_in_verified', (data) => {
    console.log(`Barge-in verified (similarity: ${data.similarity})`);
    this.handleBargeIn();
});
```

## Phase 3: UI Updates

### 3.1 Add enrollment prompt to index.html

```html
<!-- Enrollment prompt (shown after Touch to Order) -->
<div id="enrollment-prompt" class="enrollment-prompt hidden">
    <div class="enrollment-icon">🎤</div>
    <div class="enrollment-text">Please say:</div>
    <div class="enrollment-phrase">"Hello, I'd like to order"</div>
    <div class="enrollment-status">Listening...</div>
</div>
```

### 3.2 Add enrollment styles to style.css

```css
.enrollment-prompt {
    text-align: center;
    padding: 40px;
}

.enrollment-icon {
    font-size: 80px;
    margin-bottom: 20px;
    animation: pulse 1.5s ease-in-out infinite;
}

.enrollment-text {
    font-size: 20px;
    color: #86868b;
    margin-bottom: 10px;
}

.enrollment-phrase {
    font-size: 28px;
    font-weight: 600;
    color: #06c;
    margin-bottom: 20px;
}

.enrollment-status {
    font-size: 16px;
    color: #86868b;
}
```

## Phase 4: Testing

### 4.1 Test enrollment
- Tap "Touch to Order"
- Say enrollment phrase
- Verify enrollment success

### 4.2 Test barge-in filtering
- Complete enrollment
- Start ordering
- While AI speaks, have customer interrupt → should work
- While AI speaks, have other person speak → should NOT trigger barge-in

### 4.3 Test edge cases
- Enrollment with short audio
- Enrollment with noisy audio
- Barge-in with similar voices
- Multiple sessions

## Phase 5: Tuning

### 5.1 Threshold adjustment
- Monitor false positive rate (other people triggering barge-in)
- Monitor false negative rate (customer not able to interrupt)
- Adjust threshold (currently 0.7) based on results

### 5.2 Enrollment duration
- Test with 1s, 2s, 3s enrollment samples
- Find optimal duration for accuracy vs UX

### 5.3 Verification chunk size
- Test with different audio chunk sizes
- Balance between latency and accuracy

## Implementation Order

1. ✅ Create speaker_verification.py module
2. ⬜ Add enrollment endpoint to voice_agent.py
3. ⬜ Add enrollment UI to frontend
4. ⬜ Implement enrollment flow
5. ⬜ Add speaker verification to audio_data handler
6. ⬜ Modify frontend to send is_speaking flag
7. ⬜ Handle barge_in_verified event
8. ⬜ Test and tune

## Current Status

- ✅ speaker_verification.py created and tested
- ✅ SpeakerVerifier class working (77.8% accuracy, 16ms latency)
- ✅ Module integrated into voice_agent.py imports
- ✅ ConversationSession has speaker_verifier instance
- ⬜ Enrollment endpoint not yet implemented
- ⬜ Frontend enrollment flow not yet implemented
- ⬜ Barge-in filtering not yet implemented

## Next Step

Implement enrollment endpoint in voice_agent.py
