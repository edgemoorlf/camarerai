"""
Test Audio Generator
Creates synthetic PCM audio files for performance testing
"""

import os
import math
import struct
import random


def generate_sine_wave(duration_seconds=3, sample_rate=16000, frequency=1000, amplitude=0.3):
    """
    Generate synthetic PCM audio (sine wave as placeholder)

    Args:
        duration_seconds: Length of audio in seconds
        sample_rate: Sample rate in Hz (default 16000)
        frequency: Frequency of sine wave in Hz (default 1000)
        amplitude: Amplitude 0.0-1.0 (default 0.3)

    Returns:
        bytes: PCM audio data (16-bit signed integer)
    """
    samples = int(sample_rate * duration_seconds)
    audio_data = []

    for i in range(samples):
        t = i / sample_rate
        sample = int(math.sin(2 * math.pi * frequency * t) * amplitude * 32767)
        audio_data.append(struct.pack('h', sample))  # 16-bit signed

    return b''.join(audio_data)


def generate_chirp(duration_seconds=3, sample_rate=16000, f0=200, f1=2000):
    """
    Generate chirp signal (frequency sweep) - more speech-like

    Args:
        duration_seconds: Length of audio in seconds
        sample_rate: Sample rate in Hz
        f0: Start frequency
        f1: End frequency

    Returns:
        bytes: PCM audio data
    """
    samples = int(sample_rate * duration_seconds)
    audio_data = []

    for i in range(samples):
        t = i / sample_rate
        # Linear frequency sweep
        freq = f0 + (f1 - f0) * (t / duration_seconds)
        sample = int(math.sin(2 * math.pi * freq * t) * 0.3 * 32767)
        audio_data.append(struct.pack('h', sample))

    return b''.join(audio_data)


def generate_noise(duration_seconds=3, sample_rate=16000, noise_type='pink'):
    """
    Generate noise signal

    Args:
        duration_seconds: Length of audio
        sample_rate: Sample rate
        noise_type: 'white', 'pink', or 'brown'

    Returns:
        bytes: PCM audio data
    """
    samples = int(sample_rate * duration_seconds)
    audio_data = []

    if noise_type == 'white':
        for _ in range(samples):
            sample = int((random.random() * 2 - 1) * 0.2 * 32767)
            audio_data.append(struct.pack('h', sample))

    elif noise_type == 'pink':
        # Simple pink noise approximation using cumulative sum
        white = [(random.random() * 2 - 1) for _ in range(samples)]
        pink = []
        cumsum = 0
        for w in white:
            cumsum += w
            pink.append(cumsum)

        # Normalize
        max_val = max(abs(min(pink)), abs(max(pink)))
        if max_val > 0:
            pink = [p / max_val for p in pink]

        for p in pink:
            sample = int(p * 0.2 * 32767)
            audio_data.append(struct.pack('h', sample))

    else:  # brown
        cumsum = 0
        for _ in range(samples):
            cumsum += (random.random() * 2 - 1)
            sample = int(cumsum * 0.1 * 32767)
            # Clip to prevent overflow
            sample = max(-32768, min(32767, sample))
            audio_data.append(struct.pack('h', sample))

    return b''.join(audio_data)


# Test scenarios with expected duration
TEST_SCENARIOS = {
    'simple_order': {
        'text': "I'd like Kung Pao Chicken",
        'duration': 2.5,
        'frequency': 800
    },
    'complex_order': {
        'text': "I want two orders of Dan Dan Noodles, one with extra spicy",
        'duration': 4.0,
        'frequency': 900
    },
    'question': {
        'text': "What do you recommend?",
        'duration': 2.0,
        'frequency': 1000
    },
    'modification': {
        'text': "Actually, make that three instead",
        'duration': 2.5,
        'frequency': 850
    },
    'greeting': {
        'text': "Hello, I'd like to place an order",
        'duration': 2.5,
        'frequency': 750
    },
    'closing': {
        'text': "Thank you, that's all",
        'duration': 2.0,
        'frequency': 800
    }
}


def generate_all_test_audio(fixtures_dir='tests/fixtures'):
    """Generate all test audio files"""
    os.makedirs(fixtures_dir, exist_ok=True)

    print("Generating test audio files...")
    print(f"Output directory: {fixtures_dir}")
    print()

    for name, config in TEST_SCENARIOS.items():
        filepath = os.path.join(fixtures_dir, f"{name}.pcm")

        # Generate chirp signal (more interesting than pure sine)
        audio = generate_chirp(
            duration_seconds=config['duration'],
            f0=config['frequency'] - 100,
            f1=config['frequency'] + 100
        )

        with open(filepath, 'wb') as f:
            f.write(audio)

        file_size = len(audio)
        duration = file_size / (16000 * 2)  # 16-bit samples

        print(f"  {name:20s} - {duration:.1f}s - {file_size} bytes")
        print(f"    Text: \"{config['text']}\"")

    print()
    print(f"Generated {len(TEST_SCENARIOS)} test audio files")
    return list(TEST_SCENARIOS.keys())


if __name__ == '__main__':
    import sys

    # Allow custom output directory
    fixtures_dir = sys.argv[1] if len(sys.argv) > 1 else 'tests/fixtures'
    generate_all_test_audio(fixtures_dir)
