#!/usr/bin/env python3
"""
Test resemblyzer for speaker verification
Measures latency and accuracy for real-time barge-in use case
"""

import time
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path


def generate_test_audio(duration: float, f0: float, sample_rate: int = 16000) -> np.ndarray:
    """Generate synthetic voice-like audio"""
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Fundamental + harmonics
    audio = np.sin(2 * np.pi * f0 * t)
    audio += 0.5 * np.sin(2 * np.pi * 2 * f0 * t)
    audio += 0.3 * np.sin(2 * np.pi * 3 * f0 * t)
    audio += 0.2 * np.sin(2 * np.pi * 4 * f0 * t)

    # Add noise
    noise = np.random.normal(0, 0.05, len(audio))
    audio = audio + noise

    # Normalize to float32 range [-1, 1] (librosa expects float)
    audio = audio / np.max(np.abs(audio))
    audio = audio.astype(np.float32)

    return audio


def test_resemblyzer():
    """Test resemblyzer performance"""

    print("=" * 60)
    print("RESEMBLYZER SPEAKER VERIFICATION TEST")
    print("=" * 60)

    # Test 1: Model Loading
    print("\n[Test 1] Model Loading")
    print("-" * 60)
    start = time.time()
    encoder = VoiceEncoder()
    load_time = time.time() - start
    print(f"✓ Model loaded in {load_time:.2f}s")

    if load_time > 5:
        print(f"  ⚠️  Load time is high (> 5s)")
    else:
        print(f"  ✓ Load time acceptable")

    # Test 2: Embedding Extraction Latency
    print("\n[Test 2] Embedding Extraction Latency")
    print("-" * 60)

    durations = [0.5, 1.0, 2.0, 3.0]

    for duration in durations:
        audio = generate_test_audio(duration, f0=200)

        start = time.time()
        embedding = encoder.embed_utterance(audio)
        extract_time = (time.time() - start) * 1000

        print(f"\nDuration: {duration}s")
        print(f"  Extraction time: {extract_time:.1f}ms")
        print(f"  Embedding shape: {embedding.shape}")

        if extract_time < 200:
            print(f"  ✓ Acceptable for real-time (< 200ms)")
        else:
            print(f"  ⚠️  Too slow for real-time (> 200ms)")

    # Test 3: Same Speaker Verification
    print("\n[Test 3] Same Speaker Verification")
    print("-" * 60)

    # Enrollment
    enrollment_audio = generate_test_audio(2.0, f0=200)
    start = time.time()
    enrollment_embed = encoder.embed_utterance(enrollment_audio)
    enrollment_time = (time.time() - start) * 1000
    print(f"Enrollment time: {enrollment_time:.1f}ms")

    # Test same speaker with variations
    test_cases = [
        ("Same exact audio", 200, 0.0),
        ("Slight pitch variation", 205, 0.0),
        ("Moderate pitch variation", 210, 0.0),
        ("With noise", 200, 0.1),
    ]

    same_speaker_scores = []

    for desc, f0, noise_level in test_cases:
        audio = generate_test_audio(2.0, f0)
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, len(audio)).astype(np.float32)
            audio = audio + noise
            audio = np.clip(audio, -1.0, 1.0).astype(np.float32)

        start = time.time()
        test_embed = encoder.embed_utterance(audio)
        verify_time = (time.time() - start) * 1000

        # Cosine similarity
        similarity = np.dot(enrollment_embed, test_embed)
        same_speaker_scores.append(similarity)

        print(f"\n{desc}:")
        print(f"  Similarity: {similarity:.3f}")
        print(f"  Verification time: {verify_time:.1f}ms")

    print(f"\nSame speaker scores: {np.mean(same_speaker_scores):.3f} ± {np.std(same_speaker_scores):.3f}")

    # Test 4: Different Speaker Verification
    print("\n[Test 4] Different Speaker Verification")
    print("-" * 60)

    different_speakers = [
        ("Similar male voice", 210),
        ("Different male voice", 180),
        ("Higher male voice", 250),
        ("Female voice", 300),
        ("Child voice", 400),
    ]

    different_speaker_scores = []

    for desc, f0 in different_speakers:
        audio = generate_test_audio(2.0, f0)
        test_embed = encoder.embed_utterance(audio)
        similarity = np.dot(enrollment_embed, test_embed)
        different_speaker_scores.append(similarity)

        print(f"\n{desc} (F0: {f0} Hz):")
        print(f"  Similarity: {similarity:.3f}")

    print(f"\nDifferent speaker scores: {np.mean(different_speaker_scores):.3f} ± {np.std(different_speaker_scores):.3f}")

    # Test 5: Threshold Analysis
    print("\n[Test 5] Threshold Analysis")
    print("-" * 60)

    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]

    print(f"\n{'Threshold':<12} {'Same Accept':<12} {'Diff Reject':<12} {'Accuracy':<10}")
    print("-" * 60)

    best_threshold = 0.7
    best_accuracy = 0

    for threshold in thresholds:
        same_accept = sum(1 for s in same_speaker_scores if s >= threshold)
        diff_reject = sum(1 for s in different_speaker_scores if s < threshold)

        total = len(same_speaker_scores) + len(different_speaker_scores)
        accuracy = (same_accept + diff_reject) / total * 100

        print(f"{threshold:<12.1f} {same_accept}/{len(same_speaker_scores):<11} {diff_reject}/{len(different_speaker_scores):<11} {accuracy:<10.1f}%")

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = threshold

    print(f"\nBest threshold: {best_threshold} (accuracy: {best_accuracy:.1f}%)")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Model load time: {load_time:.2f}s")
    print(f"Embedding extraction: ~{extract_time:.0f}ms (for 3s audio)")
    print(f"Same speaker similarity: {np.mean(same_speaker_scores):.3f} ± {np.std(same_speaker_scores):.3f}")
    print(f"Different speaker similarity: {np.mean(different_speaker_scores):.3f} ± {np.std(different_speaker_scores):.3f}")
    print(f"Best threshold: {best_threshold}")
    print(f"Best accuracy: {best_accuracy:.1f}%")

    # Evaluation
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)

    if extract_time < 200:
        print("✓ Latency: Acceptable for real-time barge-in")
    else:
        print("⚠️  Latency: Too slow for real-time")

    if best_accuracy >= 80:
        print("✓ Accuracy: Good for POC (>= 80%)")
    else:
        print("⚠️  Accuracy: May need tuning")

    # Check separation
    separation = np.mean(same_speaker_scores) - np.mean(different_speaker_scores)
    print(f"\nScore separation: {separation:.3f}")

    if separation > 0.2:
        print("✓ Good separation between same/different speakers")
    else:
        print("⚠️  Poor separation - may have high error rate")

    print("\n" + "=" * 60)
    if best_accuracy >= 80 and extract_time < 200:
        print("✓ RESEMBLYZER IS SUITABLE FOR BARGE-IN FILTERING")
        print("\nRecommendation:")
        print(f"- Use threshold: {best_threshold}")
        print(f"- Expected accuracy: {best_accuracy:.1f}%")
        print(f"- Latency: ~{extract_time:.0f}ms")
        return True
    else:
        print("⚠️  RESEMBLYZER MAY NEED ADJUSTMENTS")
        print("\nIssues:")
        if extract_time >= 200:
            print("- Latency too high for real-time")
        if best_accuracy < 80:
            print("- Accuracy below target (80%)")
        return False


if __name__ == "__main__":
    success = test_resemblyzer()
    exit(0 if success else 1)
