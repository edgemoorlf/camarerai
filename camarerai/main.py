"""
Main Entry Point for Voice Agent
Imports and launches the appropriate voice agent based on configuration
"""

from camarerai import config

# Validate configuration
config.validate_provider_config()

# Import and run the appropriate voice agent based on provider
if config.PROVIDER == 'dashscope':
    print("=" * 60)
    print("Starting Voice Agent with DashScope Provider")
    print("=" * 60)
    print(f"ASR:  {config.ASR_PROVIDER}")
    print(f"LLM:  {config.LLM_PROVIDER}")
    print(f"TTS:  {config.TTS_PROVIDER}")
    print("=" * 60)
    from camarerai.providers.dashscope.voice_agent import app, socketio

elif config.PROVIDER == 'gemini':
    print("=" * 60)
    print("Starting Voice Agent with Gemini Provider (Standard API)")
    print("=" * 60)
    print(f"Model: gemini-1.5-flash")
    print("Note: ASR + LLM via Gemini, TTS via DashScope")
    print("=" * 60)
    from camarerai.providers.gemini.voice_agent import app, socketio

elif config.PROVIDER == 'gemini_live':
    print("=" * 60)
    print("Starting Voice Agent with Gemini Live API")
    print("=" * 60)
    print(f"Model: {config.GEMINI_LIVE_MODEL}")
    print("Note: Native bidirectional audio streaming")
    print("=" * 60)
    from camarerai.providers.gemini_live.voice_agent import app, socketio

else:
    raise ValueError(f"Unknown provider: {config.PROVIDER}. "
                     f"Use 'dashscope', 'gemini', or 'gemini_live'")

if __name__ == '__main__':
    print(f"\nServer running on http://{config.HOST}:{config.PORT}")
    print("Press Ctrl+C to stop\n")
    socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG,
                 allow_unsafe_werkzeug=True)
