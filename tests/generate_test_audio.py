#!/usr/bin/env python3
"""
Generate real speech audio for test fixtures using DashScope TTS
Replaces synthetic chirp waves with actual speech that ASR can recognize
"""

import os
import sys
import urllib.request
import ssl
import wave
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.dashscope_service import DashScopeService


# Test scenarios with text to synthesize
TEST_SCENARIOS = {
    'simple_order': "I'd like Kung Pao Chicken",
    'complex_order': "I want two orders of Dan Dan Noodles, one with extra spicy",
    'question': "What do you recommend?",
    'modification': "Actually, make that three instead",
    'greeting': "Hello, I'd like to place an order",
    'closing': "Thank you, that's all"
}


def download_audio(url, output_path):
    """Download audio from URL to file"""
    try:
        # Create SSL context that doesn't verify certificates (for some edge cases)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            audio_data = response.read()

        with open(output_path, 'wb') as f:
            f.write(audio_data)

        return len(audio_data)
    except Exception as e:
        print(f"  Error downloading: {e}")
        return 0


def wav_to_pcm(wav_data, target_sample_rate=16000):
    """
    Convert WAV data to raw PCM data at target sample rate

    Args:
        wav_data: WAV file bytes
        target_sample_rate: Target sample rate (default 16000)

    Returns:
        Raw PCM bytes at target sample rate
    """
    try:
        # Read WAV file
        wav_file = wave.open(io.BytesIO(wav_data), 'rb')

        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        num_frames = wav_file.getnframes()

        # Read raw audio data
        raw_data = wav_file.readframes(num_frames)
        wav_file.close()

        # Convert to mono if stereo
        if channels == 2:
            # Convert stereo to mono by averaging channels
            import struct
            fmt = '<hh' if sample_width == 2 else '<h'
            samples = []
            for i in range(0, len(raw_data), sample_width * 2):
                left = struct.unpack_from('<h', raw_data, i)[0]
                right = struct.unpack_from('<h', raw_data, i + sample_width)[0]
                samples.append((left + right) // 2)
            raw_data = struct.pack('<' + 'h' * len(samples), *samples)

        # Resample if needed (simple downsampling for 24kHz -> 16kHz)
        if sample_rate != target_sample_rate:
            import struct
            # For 24kHz -> 16kHz, we keep 2 out of every 3 samples
            samples = struct.unpack('<' + 'h' * (len(raw_data) // 2), raw_data)
            resampled = []
            for i in range(0, len(samples) - 2, 3):
                # Simple averaging of 3 samples into 2
                resampled.append(samples[i])
                resampled.append((samples[i+1] + samples[i+2]) // 2)
            raw_data = struct.pack('<' + 'h' * len(resampled), *resampled)

        return raw_data

    except Exception as e:
        print(f"  Error converting WAV to PCM: {e}")
        return wav_data  # Return original if conversion fails


def generate_all_test_audio(fixtures_dir='tests/fixtures'):
    """Generate all test audio files using DashScope TTS"""
    os.makedirs(fixtures_dir, exist_ok=True)

    print("="*70)
    print("Generating Test Audio with DashScope TTS")
    print("="*70)
    print(f"Output directory: {fixtures_dir}")
    print()

    # Initialize DashScope service
    try:
        service = DashScopeService()
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure DASHSCOPE_API_KEY is set in your .env file")
        return

    for name, text in TEST_SCENARIOS.items():
        filepath = os.path.join(fixtures_dir, f"{name}.pcm")
        wav_path = os.path.join(fixtures_dir, f"{name}.wav")

        print(f"Generating: {name}")
        print(f"  Text: \"{text}\"")

        try:
            # Generate TTS (non-streaming to get URL)
            audio_url = service.synthesize(
                text=text,
                voice='Cherry',
                language_type='English',
                stream=False
            )

            if audio_url:
                print(f"  URL: {audio_url[:60]}...")

                # Download the audio file
                wav_size = download_audio(audio_url, wav_path)

                if wav_size > 0:
                    print(f"  ✓ Downloaded WAV: {wav_size} bytes")

                    # Convert WAV to PCM
                    with open(wav_path, 'rb') as f:
                        wav_data = f.read()

                    pcm_data = wav_to_pcm(wav_data, target_sample_rate=16000)

                    with open(filepath, 'wb') as f:
                        f.write(pcm_data)

                    print(f"  ✓ Converted to PCM: {len(pcm_data)} bytes (16kHz mono)")

                    # Remove temporary WAV file
                    os.remove(wav_path)
                else:
                    print(f"  ✗ Failed to download")
            else:
                print(f"  ✗ No audio URL returned")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("="*70)
    print("Generation complete!")
    print("All files are raw PCM 16kHz mono 16-bit")
    print("="*70)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate test audio using DashScope TTS')
    parser.add_argument('--output', '-o', default='tests/fixtures',
                        help='Output directory for audio files')
    args = parser.parse_args()

    generate_all_test_audio(args.output)
