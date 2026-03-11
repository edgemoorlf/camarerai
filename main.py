"""
Main Entry Point for Voice Agent
Imports and launches the appropriate voice agent based on configuration
"""

import config

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
    from voice_agent_dashscope import app, socketio

elif config.PROVIDER == 'gemini':
    print("=" * 60)
    print("Starting Voice Agent with Gemini Provider (Standard API)")
    print("=" * 60)
    print(f"Model: gemini-1.5-flash")
    print("Note: ASR + LLM via Gemini, TTS via DashScope")
    print("=" * 60)
    # Import from gemini_standard when implemented
    try:
        from voice_agent_gemini_standard import app, socketio
    except ImportError as e:
        print(f"\nERROR: voice_agent_gemini_standard.py not implemented yet")
        print(f"Details: {e}")
        print("\nPlease use one of these options:")
        print("  PROVIDER=dashscope       - DashScope ASR+LLM+TTS")
        print("  PROVIDER=gemini_live     - Gemini Live API (native audio)")
        print("")
        raise SystemExit(1)

elif config.PROVIDER == 'gemini_live':
    print("=" * 60)
    print("Starting Voice Agent with Gemini Live API")
    print("=" * 60)
    print(f"Model: {config.GEMINI_LIVE_MODEL}")
    print("Note: Native bidirectional audio streaming")
    print("=" * 60)
    from voice_agent_gemini_live import app, socketio

else:
    raise ValueError(f"Unknown provider: {config.PROVIDER}. "
                     f"Use 'dashscope', 'gemini', or 'gemini_live'")

if __name__ == '__main__':
    print(f"\nServer running on http://{config.HOST}:{config.PORT}")
    print("Press Ctrl+C to stop\n")
    socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG)
