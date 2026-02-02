# Audio Transcription Fix - Summary

## Problem
The DashScope ASR API was failing with a 400 error because:
1. The updated DashScope SDK (v1.24.6+) uses `Transcription.async_call()` which requires a **URL** to the audio file, not a local file path
2. The original code was passing a local file path (`/tmp/uuid.wav`) directly to the API

## Solution
Updated `poc_voice_agent.py` to:

1. **Save audio file locally** with a unique ID
2. **Serve the file via Flask endpoint** at `/api/audio/<file_id>`
3. **Generate a URL** that DashScope can access (e.g., `http://localhost:5002/api/audio/uuid`)
4. **Pass the URL** to DashScope ASR
5. **Clean up** the temporary file after transcription

## Changes Made

### 1. Added imports and storage
```python
from flask import Flask, render_template, request, jsonify, send_file, url_for
import tempfile

# Temporary audio file storage (for serving to DashScope)
temp_audio_files = {}
```

### 2. Updated `/api/voice/transcribe` endpoint
- Saves audio with unique ID
- Creates accessible URL for DashScope
- Cleans up after transcription

### 3. Added `/api/audio/<file_id>` endpoint
- Serves temporary audio files to DashScope
- Returns 404 if file not found

### 4. Updated `/api/voice/synthesize` endpoint
- Uses new DashScope TTS API parameters
- `voice='Cherry'` instead of `voice_id`
- `language_type='Auto'` for automatic language detection

## Testing

Restart the application and test:

```bash
# Stop the current server (Ctrl+C)
# Restart
python3 poc_voice_agent.py
```

Then in the browser:
1. Click "Tap to Talk"
2. Speak into microphone
3. Check browser console for any errors
4. Verify transcription appears

## Expected Flow

1. **User speaks** → Browser records audio
2. **Audio uploaded** → POST to `/api/voice/transcribe`
3. **File saved** → Temporary file with unique ID
4. **URL created** → `http://localhost:5002/api/audio/{file_id}`
5. **DashScope called** → ASR transcribes from URL
6. **Text returned** → Displayed in UI
7. **File cleaned up** → Temporary file deleted

## Additional Notes

- The server must be accessible from the internet if DashScope needs to fetch the URL
- For local testing, this should work fine
- For production, consider using OSS (Object Storage Service) instead of serving files directly
