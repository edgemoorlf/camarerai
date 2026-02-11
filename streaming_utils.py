def has_sentence_ending(text):
    """
    Detect sentence boundaries for streaming TTS

    Returns True if text ends with a sentence boundary marker
    """
    if not text or not text.strip():
        return False

    text = text.strip()

    # Sentence endings
    sentence_endings = (
        '.', '!', '?',      # English
        '。', '！', '？',    # Chinese
        '．', '！', '？'     # Full-width
    )

    # Also consider commas and pauses for faster streaming
    # This allows TTS to start even before full sentence
    pause_markers = (
        ',', '，', '、',     # Commas
        ';', '；',           # Semicolons
    )

    # Check for sentence endings (higher priority)
    if any(text.endswith(e) for e in sentence_endings):
        return True

    # Check for pause markers (lower priority, but still useful)
    # Only trigger if we have enough text (avoid too-short chunks)
    if len(text) > 15 and any(text.endswith(p) for p in pause_markers):
        return True

    return False
