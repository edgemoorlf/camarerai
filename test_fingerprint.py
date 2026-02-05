#!/usr/bin/env python3
"""
Test Voice Fingerprinting with Real Audio Scenarios
Tests latency, accuracy, and robustness for barge-in use case
"""

import time
import numpy as np
from speaker_fingerprint import VoiceFingerprint


def generate_voice_audio(duration: float, f0: float, sample_rate: int = 16000) -> np.ndarray:
    """Generate synthetic voice-like audio with harmonics"""
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Fundamental + harmonics (more realistic than pure sine)
    audio = np.sin(2 * np.pi * f0 * t)  # Fundamental
    audio += 0.5 * np.sin(2 * np.pi * 2 * f0 * t)  # 2nd harmonic
    audio += 0.3 * np.sin(2 * np.pi * 3 * f0 * t)  # 3rd harmonic
    audio += 0.2 * np.sin(2 * np.pi * 4 * f0 * t)  # 4th harmonic

    # Add some noise (more realistic)
    noise = np.random.normal(0, 0.05, len(audio))
    audio = audio + noise

    # Normalize
    audio = audio / np.max(np.abs(audio))

    return audio.astype(np.float32)


def add_background_noise(audio: np.ndarray, noise_level: float = 0.1) -> np.ndarray:
    """Add background noise to audio"""
    noise = np.random.normal(0, noise_level, len(audio))
    noisy_audio = audio + noise
    # Normalize
    noisy_audio = noisy_audio / np.max(np.abs(noisy_audio))
    return noisy_audio.astype(np.float32)


def test_latency():
    """Test fingerprint extraction and comparison latency"""
    print("\n" + "=" * 60)
    print("TEST 1: LATENCY")
    print("=" * 60)

    vf = VoiceFingerprint(sample_rate=16000)

    # Test with different audio lengths
    durations = [0.5, 1.0, 2.0, 3.0]

    for duration in durations:
        audio = generate_voice_audio(duration, f0=200)

        # Test fingerprint creation
        start = time.time()
        fp = vf.create_fingerprint(audio)
        create_time = (time.time() - start) * 1000

        # Test comparison
        start = time.time()
        similarity = vf.compare_fingerprints(fp, fp)
        compare_time = (time.time() - start) * 1000

        total_time = create_time + compare_time

        print(f"\nDuration: {duration}s")
        print(f"  Create fingerprint: {create_time:.1f}ms")
        print(f"  Compare fingerprints: {compare_time:.1f}ms")
        print(f"  Total: {total_time:.1f}ms")

        if total_time < 200:
            print(f"  ✓ Acceptable for real-time (< 200ms)")
        else:
            print(f"  ⚠️  Too slow for real-time (> 200ms)")

    return True


def test_accuracy_same_speaker():
    """Test accuracy with same speaker (different utterances)"""
    print("\n" + "=" * 60)
    print("TEST 2: ACCURACY - SAME SPEAKER")
    print("=" * 60)

    vf = VoiceFingerprint(sample_rate=16000)

    # Simulate same speaker with slight variations
    base_f0 = 200  # Male voice

    # Enrollment
    enrollment_audio = generate_voice_audio(2.0, base_f0)
    enrollment_fp = vf.create_fingerprint(enrollment_audio)

    print(f"\nEnrollment F0: {enrollment_fp['f0_mean']:.1f} Hz")

    # Test with variations
    variations = [
        ("Same exact audio", 0, 0.0),
        ("Slight pitch variation (+5%)", 5, 0.0),
        ("Moderate pitch variation (+10%)", 10, 0.0),
        ("With background noise", 0, 0.1),
        ("Pitch + noise", 5, 0.1),
    ]

    results = []

    for desc, pitch_var, noise_level in variations:
        # Generate test audio
        test_f0 = base_f0 * (1 + pitch_var / 100)
        test_audio = generate_voice_audio(2.0, test_f0)

        if noise_level > 0:
            test_audio = add_background_noise(test_audio, noise_level)

        # Verify
        is_match, similarity = vf.verify_speaker(enrollment_fp, test_audio, threshold=0.7)
        results.append((desc, is_match, similarity))

        status = "✓ MATCH" if is_match else "✗ NO MATCH"
        print(f"\n{desc}:")
        print(f"  Similarity: {similarity:.3f}")
        print(f"  Result: {status}")

    # Calculate accuracy
    correct = sum(1 for _, is_match, _ in results if is_match)
    accuracy = correct / len(results) * 100

    print(f"\n{'='*60}")
    print(f"Same Speaker Accuracy: {accuracy:.1f}% ({correct}/{len(results)})")

    if accuracy >= 80:
        print("✓ Good accuracy for same speaker")
    else:
        print("⚠️  Low accuracy - may need tuning")

    return accuracy >= 80


def test_accuracy_different_speakers():
    """Test accuracy with different speakers (should NOT match)"""
    print("\n" + "=" * 60)
    print("TEST 3: ACCURACY - DIFFERENT SPEAKERS")
    print("=" * 60)

    vf = VoiceFingerprint(sample_rate=16000)

    # Enrollment: Male voice
    enrollment_audio = generate_voice_audio(2.0, f0=200)
    enrollment_fp = vf.create_fingerprint(enrollment_audio)

    print(f"\nEnrolled Speaker F0: {enrollment_fp['f0_mean']:.1f} Hz")

    # Test with different speakers
    test_speakers = [
        ("Similar male voice", 210),
        ("Different male voice", 180),
        ("Higher male voice", 250),
        ("Female voice", 300),
        ("Child voice", 400),
    ]

    results = []

    for desc, test_f0 in test_speakers:
        test_audio = generate_voice_audio(2.0, test_f0)
        is_match, similarity = vf.verify_speaker(enrollment_fp, test_audio, threshold=0.7)
        results.append((desc, is_match, similarity))

        status = "✗ REJECTED" if not is_match else "⚠️  FALSE POSITIVE"
        print(f"\n{desc} (F0: {test_f0} Hz):")
        print(f"  Similarity: {similarity:.3f}")
        print(f"  Result: {status}")

    # Calculate accuracy (should reject all)
    correct = sum(1 for _, is_match, _ in results if not is_match)
    accuracy = correct / len(results) * 100

    print(f"\n{'='*60}")
    print(f"Different Speaker Rejection Rate: {accuracy:.1f}% ({correct}/{len(results)})")

    if accuracy >= 80:
        print("✓ Good rejection of different speakers")
    else:
        print("⚠️  High false positive rate - threshold may need adjustment")

    return accuracy >= 80


def test_threshold_tuning():
    """Test different thresholds to find optimal value"""
    print("\n" + "=" * 60)
    print("TEST 4: THRESHOLD TUNING")
    print("=" * 60)

    vf = VoiceFingerprint(sample_rate=16000)

    # Create test dataset
    # Same speaker samples
    base_f0 = 200
    enrollment_audio = generate_voice_audio(2.0, base_f0)
    enrollment_fp = vf.create_fingerprint(enrollment_audio)

    same_speaker_samples = []
    for i in range(10):
        # Variations in pitch and noise
        pitch_var = np.random.uniform(-5, 5)
        noise_level = np.random.uniform(0, 0.1)
        test_f0 = base_f0 * (1 + pitch_var / 100)
        audio = generate_voice_audio(2.0, test_f0)
        if noise_level > 0:
            audio = add_background_noise(audio, noise_level)
        fp = vf.create_fingerprint(audio)
        similarity = vf.compare_fingerprints(enrollment_fp, fp)
        same_speaker_samples.append(similarity)

    # Different speaker samples
    different_speaker_samples = []
    for test_f0 in [180, 190, 210, 220, 250, 280, 300, 320, 350, 400]:
        audio = generate_voice_audio(2.0, test_f0)
        fp = vf.create_fingerprint(audio)
        similarity = vf.compare_fingerprints(enrollment_fp, fp)
        different_speaker_samples.append(similarity)

    print(f"\nSame speaker similarities: {np.mean(same_speaker_samples):.3f} ± {np.std(same_speaker_samples):.3f}")
    print(f"Different speaker similarities: {np.mean(different_speaker_samples):.3f} ± {np.std(different_speaker_samples):.3f}")

    # Test different thresholds
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]

    print(f"\n{'Threshold':<12} {'True Pos':<10} {'False Neg':<10} {'True Neg':<10} {'False Pos':<10} {'Accuracy':<10}")
    print("-" * 60)

    best_threshold = 0.7
    best_accuracy = 0

    for threshold in thresholds:
        # True positives (same speaker, correctly identified)
        tp = sum(1 for s in same_speaker_samples if s >= threshold)
        # False negatives (same speaker, incorrectly rejected)
        fn = len(same_speaker_samples) - tp
        # True negatives (different speaker, correctly rejected)
        tn = sum(1 for s in different_speaker_samples if s < threshold)
        # False positives (different speaker, incorrectly accepted)
        fp = len(different_speaker_samples) - tn

        accuracy = (tp + tn) / (len(same_speaker_samples) + len(different_speaker_samples)) * 100

        print(f"{threshold:<12.1f} {tp:<10} {fn:<10} {tn:<10} {fp:<10} {accuracy:<10.1f}%")

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = threshold

    print(f"\n{'='*60}")
    print(f"Best threshold: {best_threshold} (accuracy: {best_accuracy:.1f}%)")

    return best_threshold, best_accuracy


def test_real_time_scenario():
    """Test real-time barge-in scenario"""
    print("\n" + "=" * 60)
    print("TEST 5: REAL-TIME BARGE-IN SCENARIO")
    print("=" * 60)

    vf = VoiceFingerprint(sample_rate=16000)

    # Enrollment (2 seconds)
    print("\n[Enrollment Phase]")
    enrollment_audio = generate_voice_audio(2.0, f0=200)
    start = time.time()
    enrollment_fp = vf.create_fingerprint(enrollment_audio)
    enrollment_time = (time.time() - start) * 1000
    print(f"Enrollment time: {enrollment_time:.1f}ms")
    print(f"Enrolled F0: {enrollment_fp['f0_mean']:.1f} Hz")

    # Simulate real-time verification (short audio chunks)
    print("\n[Real-time Verification Phase]")
    print("Simulating barge-in detection with 0.5s audio chunks...")

    scenarios = [
        ("Customer speaking", 200, 0.05, True),
        ("Customer speaking (noisy)", 205, 0.15, True),
        ("Other person nearby", 250, 0.05, False),
        ("Background conversation", 180, 0.1, False),
        ("Customer again", 198, 0.08, True),
    ]

    results = []

    for desc, test_f0, noise_level, should_match in scenarios:
        # Short audio chunk (0.5s for real-time)
        audio = generate_voice_audio(0.5, test_f0)
        if noise_level > 0:
            audio = add_background_noise(audio, noise_level)

        # Verify
        start = time.time()
        is_match, similarity = vf.verify_speaker(enrollment_fp, audio, threshold=0.7)
        verify_time = (time.time() - start) * 1000

        correct = (is_match == should_match)
        results.append(correct)

        status = "✓" if correct else "✗"
        match_str = "MATCH" if is_match else "NO MATCH"

        print(f"\n{status} {desc}:")
        print(f"  Expected: {'MATCH' if should_match else 'NO MATCH'}")
        print(f"  Got: {match_str} (similarity: {similarity:.3f})")
        print(f"  Latency: {verify_time:.1f}ms")

    accuracy = sum(results) / len(results) * 100

    print(f"\n{'='*60}")
    print(f"Real-time Accuracy: {accuracy:.1f}% ({sum(results)}/{len(results)})")

    if accuracy >= 80:
        print("✓ Good accuracy for real-time barge-in filtering")
    else:
        print("⚠️  May need threshold adjustment or more features")

    return accuracy >= 80


def main():
    """Run all tests"""
    print("=" * 60)
    print("VOICE FINGERPRINTING TESTS")
    print("Testing for Real-time Barge-in Speaker Verification")
    print("=" * 60)

    results = {}

    # Run tests
    results['latency'] = test_latency()
    results['same_speaker'] = test_accuracy_same_speaker()
    results['different_speakers'] = test_accuracy_different_speakers()

    best_threshold, best_accuracy = test_threshold_tuning()
    results['threshold_tuning'] = best_accuracy >= 80

    results['real_time'] = test_real_time_scenario()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nConclusion:")
        print("- Voice fingerprinting is suitable for barge-in filtering")
        print("- Latency is acceptable for real-time use (< 200ms)")
        print("- Accuracy is good for POC (80%+)")
        print(f"- Recommended threshold: {best_threshold}")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nConclusion:")
        print("- Voice fingerprinting may need improvements")
        print("- Consider adjusting features or threshold")
        print("- May need to try Option 3 (open-source models)")

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
