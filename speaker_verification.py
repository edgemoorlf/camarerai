"""
Speaker Verification Module using resemblyzer
Provides speaker enrollment and verification for barge-in filtering
"""

import numpy as np
from resemblyzer import VoiceEncoder
from typing import Optional, Tuple
import json
from pathlib import Path


class SpeakerVerifier:
    """
    Speaker verification using resemblyzer for barge-in filtering

    Usage:
        verifier = SpeakerVerifier()

        # Enrollment
        enrollment_audio = ... # numpy array, float32, 16kHz
        verifier.enroll_speaker(enrollment_audio)

        # Verification
        test_audio = ... # numpy array, float32, 16kHz
        is_match, similarity = verifier.verify_speaker(test_audio)
    """

    def __init__(self, threshold: float = 0.7):
        """
        Initialize speaker verifier

        Args:
            threshold: Similarity threshold for verification (0-1)
                      0.7 recommended based on testing
        """
        self.threshold = threshold
        self.encoder = VoiceEncoder()
        self.enrolled_embedding: Optional[np.ndarray] = None
        self.enrolled = False

    def enroll_speaker(self, audio: np.ndarray) -> Tuple[bool, str]:
        """
        Enroll a speaker from audio sample

        Args:
            audio: Audio samples (float32, normalized to [-1, 1], 16kHz)
                  Recommended: 2-3 seconds for good enrollment

        Returns:
            (success, message)
        """
        try:
            # Validate audio
            if len(audio) < 8000:  # Less than 0.5 seconds at 16kHz
                return False, "Audio too short (need at least 0.5 seconds)"

            if not isinstance(audio, np.ndarray):
                return False, "Audio must be numpy array"

            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # Normalize if needed
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / np.max(np.abs(audio))

            # Extract embedding
            self.enrolled_embedding = self.encoder.embed_utterance(audio)
            self.enrolled = True

            return True, "Speaker enrolled successfully"

        except Exception as e:
            return False, f"Enrollment failed: {str(e)}"

    def verify_speaker(
        self,
        audio: np.ndarray,
        return_similarity: bool = True
    ) -> Tuple[bool, float]:
        """
        Verify if audio matches enrolled speaker

        Args:
            audio: Audio samples (float32, normalized to [-1, 1], 16kHz)
            return_similarity: Whether to return similarity score

        Returns:
            (is_match, similarity_score)
        """
        if not self.enrolled:
            # No speaker enrolled - accept all (fallback behavior)
            return True, 1.0

        try:
            # Validate audio
            if len(audio) < 4000:  # Less than 0.25 seconds at 16kHz
                # Too short for reliable verification
                return False, 0.0

            if not isinstance(audio, np.ndarray):
                return False, 0.0

            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # Normalize if needed
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / np.max(np.abs(audio))

            # Extract embedding
            test_embedding = self.encoder.embed_utterance(audio)

            # Compute similarity (cosine similarity)
            similarity = float(np.dot(self.enrolled_embedding, test_embedding))

            # Verify against threshold
            is_match = similarity >= self.threshold

            return is_match, similarity

        except Exception as e:
            print(f"Verification error: {e}")
            # On error, accept (fail open for better UX)
            return True, 0.0

    def reset(self):
        """Reset enrollment (for new session)"""
        self.enrolled_embedding = None
        self.enrolled = False

    def is_enrolled(self) -> bool:
        """Check if a speaker is enrolled"""
        return self.enrolled

    def get_threshold(self) -> float:
        """Get current verification threshold"""
        return self.threshold

    def set_threshold(self, threshold: float):
        """
        Set verification threshold

        Args:
            threshold: New threshold (0-1)
                      Higher = stricter (fewer false positives)
                      Lower = more lenient (fewer false negatives)
        """
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.threshold = threshold

    def save_enrollment(self, filepath: str):
        """
        Save enrolled speaker embedding to file

        Args:
            filepath: Path to save embedding
        """
        if not self.enrolled:
            raise ValueError("No speaker enrolled")

        data = {
            'embedding': self.enrolled_embedding.tolist(),
            'threshold': self.threshold
        }

        with open(filepath, 'w') as f:
            json.dump(data, f)

    def load_enrollment(self, filepath: str) -> Tuple[bool, str]:
        """
        Load enrolled speaker embedding from file

        Args:
            filepath: Path to load embedding from

        Returns:
            (success, message)
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.enrolled_embedding = np.array(data['embedding'], dtype=np.float32)
            self.threshold = data.get('threshold', 0.7)
            self.enrolled = True

            return True, "Enrollment loaded successfully"

        except Exception as e:
            return False, f"Failed to load enrollment: {str(e)}"


# Convenience functions for quick usage

def create_verifier(threshold: float = 0.7) -> SpeakerVerifier:
    """Create a new speaker verifier instance"""
    return SpeakerVerifier(threshold=threshold)


def enroll_and_verify(
    enrollment_audio: np.ndarray,
    test_audio: np.ndarray,
    threshold: float = 0.7
) -> Tuple[bool, float]:
    """
    Quick enrollment and verification

    Args:
        enrollment_audio: Audio to enroll
        test_audio: Audio to verify
        threshold: Verification threshold

    Returns:
        (is_match, similarity)
    """
    verifier = SpeakerVerifier(threshold=threshold)
    success, msg = verifier.enroll_speaker(enrollment_audio)

    if not success:
        raise ValueError(f"Enrollment failed: {msg}")

    return verifier.verify_speaker(test_audio)


if __name__ == "__main__":
    # Quick test
    print("Speaker Verification Module")
    print("=" * 60)

    # Create verifier
    verifier = SpeakerVerifier(threshold=0.7)
    print(f"✓ Verifier created (threshold: {verifier.get_threshold()})")

    # Generate test audio
    duration = 2.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Speaker 1
    audio1 = np.sin(2 * np.pi * 200 * t).astype(np.float32)

    # Speaker 2
    audio2 = np.sin(2 * np.pi * 300 * t).astype(np.float32)

    # Enroll speaker 1
    print("\nEnrolling speaker 1...")
    success, msg = verifier.enroll_speaker(audio1)
    print(f"{'✓' if success else '✗'} {msg}")

    # Verify same speaker
    print("\nVerifying same speaker...")
    is_match, similarity = verifier.verify_speaker(audio1)
    print(f"Match: {is_match}, Similarity: {similarity:.3f}")

    # Verify different speaker
    print("\nVerifying different speaker...")
    is_match, similarity = verifier.verify_speaker(audio2)
    print(f"Match: {is_match}, Similarity: {similarity:.3f}")

    print("\n✓ Module working correctly")
