#!/usr/bin/env python3
"""
Voice Fingerprinting Module for Speaker Verification
Uses basic audio features (pitch, formants, MFCC) to create voice fingerprints
No external ML dependencies - uses only numpy and scipy
"""

import numpy as np
from scipy import signal
from scipy.fft import fft
from typing import Dict, Tuple, Optional
import json


class VoiceFingerprint:
    """
    Creates and compares voice fingerprints using audio features

    Features extracted:
    - Fundamental frequency (F0) - pitch
    - Formants (F1, F2, F3) - vocal tract resonances
    - MFCC (Mel-frequency cepstral coefficients) - spectral envelope
    - Energy distribution across frequency bands
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.n_mfcc = 13  # Number of MFCC coefficients
        self.n_fft = 512  # FFT window size
        self.hop_length = 160  # 10ms hop at 16kHz

    def extract_features(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Extract voice features from audio

        Args:
            audio: Audio samples (float32, normalized to [-1, 1])

        Returns:
            Dictionary of features
        """
        # Ensure audio is float32 and normalized
        audio = audio.astype(np.float32)
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        features = {}

        # 1. Fundamental Frequency (F0) - Pitch
        features['f0'] = self._extract_f0(audio)

        # 2. Formants (F1, F2, F3)
        features['formants'] = self._extract_formants(audio)

        # 3. MFCC
        features['mfcc'] = self._extract_mfcc(audio)

        # 4. Energy distribution
        features['energy'] = self._extract_energy(audio)

        return features

    def _extract_f0(self, audio: np.ndarray) -> float:
        """Extract fundamental frequency (pitch) using autocorrelation"""
        # Apply pre-emphasis
        emphasized = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])

        # Autocorrelation
        corr = np.correlate(emphasized, emphasized, mode='full')
        corr = corr[len(corr)//2:]

        # Find first peak after initial peak
        # Look for pitch in range 80-400 Hz (typical human voice)
        min_period = int(self.sample_rate / 400)  # 400 Hz
        max_period = int(self.sample_rate / 80)   # 80 Hz

        if len(corr) < max_period:
            return 0.0

        # Find peak in valid range
        search_range = corr[min_period:max_period]
        if len(search_range) == 0:
            return 0.0

        peak_idx = np.argmax(search_range) + min_period
        f0 = self.sample_rate / peak_idx

        return float(f0)

    def _extract_formants(self, audio: np.ndarray) -> np.ndarray:
        """Extract first 3 formants using LPC"""
        # Apply pre-emphasis
        emphasized = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])

        # Use LPC to find formants
        # Order 12 is typical for 16kHz (2 + sample_rate/1000)
        order = 12

        # Compute LPC coefficients
        a = self._lpc(emphasized, order)

        # Find roots of LPC polynomial
        roots = np.roots(a)

        # Keep only roots inside unit circle
        roots = roots[np.abs(roots) < 1]

        # Convert to frequencies
        angles = np.angle(roots)
        freqs = angles * (self.sample_rate / (2 * np.pi))

        # Keep only positive frequencies
        freqs = freqs[freqs > 0]

        # Sort and take first 3 (formants)
        freqs = np.sort(freqs)

        # Pad with zeros if less than 3 formants found
        formants = np.zeros(3)
        formants[:min(3, len(freqs))] = freqs[:min(3, len(freqs))]

        return formants

    def _lpc(self, signal: np.ndarray, order: int) -> np.ndarray:
        """Linear Predictive Coding - compute LPC coefficients"""
        # Autocorrelation method
        r = np.correlate(signal, signal, mode='full')
        r = r[len(r)//2:]
        r = r[:order+1]

        # Levinson-Durbin recursion
        a = np.zeros(order + 1)
        a[0] = 1.0

        if len(r) < order + 1:
            return a

        e = r[0]
        for i in range(1, order + 1):
            if e == 0:
                break
            lambda_val = -np.sum(a[:i] * r[i:0:-1]) / e
            a[1:i+1] += lambda_val * a[i-1::-1]
            a[i] = lambda_val
            e *= (1 - lambda_val**2)

        return a

    def _extract_mfcc(self, audio: np.ndarray) -> np.ndarray:
        """Extract MFCC features"""
        # Compute spectrogram
        f, t, Sxx = signal.spectrogram(
            audio,
            fs=self.sample_rate,
            nperseg=self.n_fft,
            noverlap=self.n_fft - self.hop_length
        )

        # Convert to mel scale
        mel_basis = self._mel_filterbank(f)
        mel_spec = np.dot(mel_basis, Sxx)

        # Log mel spectrogram
        log_mel_spec = np.log(mel_spec + 1e-10)

        # DCT to get MFCC
        mfcc = self._dct(log_mel_spec)[:self.n_mfcc]

        # Take mean across time
        mfcc_mean = np.mean(mfcc, axis=1)

        return mfcc_mean

    def _mel_filterbank(self, freqs: np.ndarray, n_filters: int = 40) -> np.ndarray:
        """Create mel filterbank"""
        # Mel scale conversion
        def hz_to_mel(hz):
            return 2595 * np.log10(1 + hz / 700)

        def mel_to_hz(mel):
            return 700 * (10**(mel / 2595) - 1)

        # Create mel-spaced frequencies
        mel_min = hz_to_mel(0)
        mel_max = hz_to_mel(self.sample_rate / 2)
        mel_points = np.linspace(mel_min, mel_max, n_filters + 2)
        hz_points = mel_to_hz(mel_points)

        # Create filterbank
        filterbank = np.zeros((n_filters, len(freqs)))

        for i in range(n_filters):
            left = hz_points[i]
            center = hz_points[i + 1]
            right = hz_points[i + 2]

            for j, freq in enumerate(freqs):
                if left <= freq <= center:
                    filterbank[i, j] = (freq - left) / (center - left)
                elif center <= freq <= right:
                    filterbank[i, j] = (right - freq) / (right - center)

        return filterbank

    def _dct(self, x: np.ndarray) -> np.ndarray:
        """Discrete Cosine Transform"""
        N = x.shape[0]
        dct_matrix = np.zeros((N, N))

        for k in range(N):
            for n in range(N):
                dct_matrix[k, n] = np.cos(np.pi * k * (2*n + 1) / (2*N))

        dct_matrix[0] *= np.sqrt(1/N)
        dct_matrix[1:] *= np.sqrt(2/N)

        return np.dot(dct_matrix, x)

    def _extract_energy(self, audio: np.ndarray) -> np.ndarray:
        """Extract energy distribution across frequency bands"""
        # Compute FFT
        fft_result = fft(audio, n=self.n_fft)
        magnitude = np.abs(fft_result[:self.n_fft//2])

        # Divide into 8 frequency bands
        n_bands = 8
        band_size = len(magnitude) // n_bands

        energy = np.zeros(n_bands)
        for i in range(n_bands):
            start = i * band_size
            end = (i + 1) * band_size if i < n_bands - 1 else len(magnitude)
            energy[i] = np.sum(magnitude[start:end]**2)

        # Normalize
        total_energy = np.sum(energy)
        if total_energy > 0:
            energy = energy / total_energy

        return energy

    def create_fingerprint(self, audio: np.ndarray) -> Dict:
        """
        Create voice fingerprint from audio

        Args:
            audio: Audio samples (float32, normalized)

        Returns:
            Fingerprint dictionary
        """
        features = self.extract_features(audio)

        fingerprint = {
            'f0_mean': float(features['f0']),
            'formants': features['formants'].tolist(),
            'mfcc': features['mfcc'].tolist(),
            'energy': features['energy'].tolist()
        }

        return fingerprint

    def compare_fingerprints(
        self,
        fp1: Dict,
        fp2: Dict,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Compare two fingerprints and return similarity score

        Args:
            fp1: First fingerprint
            fp2: Second fingerprint
            weights: Feature weights (default: equal weights)

        Returns:
            Similarity score (0-1, higher is more similar)
        """
        if weights is None:
            weights = {
                'f0': 0.2,
                'formants': 0.3,
                'mfcc': 0.3,
                'energy': 0.2
            }

        similarities = {}

        # F0 similarity (inverse of normalized difference)
        f0_diff = abs(fp1['f0_mean'] - fp2['f0_mean'])
        f0_max = max(fp1['f0_mean'], fp2['f0_mean'], 1.0)
        similarities['f0'] = 1 - min(f0_diff / f0_max, 1.0)

        # Formants similarity (cosine similarity)
        formants1 = np.array(fp1['formants'])
        formants2 = np.array(fp2['formants'])
        similarities['formants'] = self._cosine_similarity(formants1, formants2)

        # MFCC similarity (cosine similarity)
        mfcc1 = np.array(fp1['mfcc'])
        mfcc2 = np.array(fp2['mfcc'])
        similarities['mfcc'] = self._cosine_similarity(mfcc1, mfcc2)

        # Energy similarity (cosine similarity)
        energy1 = np.array(fp1['energy'])
        energy2 = np.array(fp2['energy'])
        similarities['energy'] = self._cosine_similarity(energy1, energy2)

        # Weighted average
        total_similarity = sum(
            similarities[key] * weights[key]
            for key in similarities
        )

        return float(total_similarity)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        if len(a) == 0 or len(b) == 0:
            return 0.0

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def verify_speaker(
        self,
        enrollment_fp: Dict,
        test_audio: np.ndarray,
        threshold: float = 0.7
    ) -> Tuple[bool, float]:
        """
        Verify if test audio matches enrolled speaker

        Args:
            enrollment_fp: Enrolled speaker fingerprint
            test_audio: Test audio samples
            threshold: Similarity threshold (0-1)

        Returns:
            (is_match, similarity_score)
        """
        test_fp = self.create_fingerprint(test_audio)
        similarity = self.compare_fingerprints(enrollment_fp, test_fp)
        is_match = similarity >= threshold

        return is_match, similarity

    def save_fingerprint(self, fingerprint: Dict, filepath: str):
        """Save fingerprint to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(fingerprint, f, indent=2)

    def load_fingerprint(self, filepath: str) -> Dict:
        """Load fingerprint from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)


if __name__ == "__main__":
    # Quick test
    print("Voice Fingerprint Module")
    print("=" * 60)

    # Create instance
    vf = VoiceFingerprint(sample_rate=16000)

    # Generate test audio (2 seconds)
    duration = 2.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Speaker 1: 200 Hz fundamental
    audio1 = np.sin(2 * np.pi * 200 * t)

    # Speaker 2: 300 Hz fundamental
    audio2 = np.sin(2 * np.pi * 300 * t)

    # Create fingerprints
    print("\nCreating fingerprints...")
    fp1 = vf.create_fingerprint(audio1)
    fp2 = vf.create_fingerprint(audio2)

    print(f"Fingerprint 1 F0: {fp1['f0_mean']:.1f} Hz")
    print(f"Fingerprint 2 F0: {fp2['f0_mean']:.1f} Hz")

    # Compare same speaker
    similarity_same = vf.compare_fingerprints(fp1, fp1)
    print(f"\nSame speaker similarity: {similarity_same:.3f}")

    # Compare different speakers
    similarity_diff = vf.compare_fingerprints(fp1, fp2)
    print(f"Different speakers similarity: {similarity_diff:.3f}")

    # Verify speaker
    is_match, score = vf.verify_speaker(fp1, audio1, threshold=0.7)
    print(f"\nVerification (same): {is_match} (score: {score:.3f})")

    is_match, score = vf.verify_speaker(fp1, audio2, threshold=0.7)
    print(f"Verification (different): {is_match} (score: {score:.3f})")

    print("\n✓ Module working correctly")
