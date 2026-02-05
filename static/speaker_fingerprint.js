/**
 * Client-Side Voice Fingerprinting for Speaker Verification
 *
 * Implements lightweight voice fingerprinting using Web Audio API
 * for real-time barge-in filtering without network latency.
 *
 * Features extracted:
 * - Fundamental frequency (F0) - pitch
 * - Spectral centroid - brightness
 * - Zero crossing rate - noisiness
 * - Energy distribution - frequency bands
 */

class VoiceFingerprint {
    constructor(sampleRate = 16000) {
        this.sampleRate = sampleRate;
        this.fftSize = 2048;
        this.minFreq = 80;   // Min human voice frequency
        this.maxFreq = 400;  // Max human voice frequency
    }

    /**
     * Extract voice features from audio data
     * @param {Float32Array} audioData - Audio samples
     * @returns {Object} Feature vector
     */
    extractFeatures(audioData) {
        if (audioData.length < 1024) {
            return null; // Too short
        }

        const features = {
            f0: this.extractF0(audioData),
            spectralCentroid: this.extractSpectralCentroid(audioData),
            zcr: this.extractZeroCrossingRate(audioData),
            energy: this.extractEnergyDistribution(audioData)
        };

        return features;
    }

    /**
     * Extract fundamental frequency (pitch) using autocorrelation
     */
    extractF0(audioData) {
        // Apply pre-emphasis
        const emphasized = new Float32Array(audioData.length);
        emphasized[0] = audioData[0];
        for (let i = 1; i < audioData.length; i++) {
            emphasized[i] = audioData[i] - 0.97 * audioData[i - 1];
        }

        // Autocorrelation
        const maxLag = Math.floor(this.sampleRate / this.minFreq);
        const minLag = Math.floor(this.sampleRate / this.maxFreq);

        let maxCorr = -Infinity;
        let bestLag = minLag;

        for (let lag = minLag; lag < maxLag && lag < audioData.length / 2; lag++) {
            let corr = 0;
            for (let i = 0; i < audioData.length - lag; i++) {
                corr += emphasized[i] * emphasized[i + lag];
            }

            if (corr > maxCorr) {
                maxCorr = corr;
                bestLag = lag;
            }
        }

        const f0 = this.sampleRate / bestLag;
        return f0;
    }

    /**
     * Extract spectral centroid (brightness)
     */
    extractSpectralCentroid(audioData) {
        const spectrum = this.computeSpectrum(audioData);

        let weightedSum = 0;
        let totalMagnitude = 0;

        for (let i = 0; i < spectrum.length; i++) {
            const freq = (i * this.sampleRate) / this.fftSize;
            weightedSum += freq * spectrum[i];
            totalMagnitude += spectrum[i];
        }

        return totalMagnitude > 0 ? weightedSum / totalMagnitude : 0;
    }

    /**
     * Extract zero crossing rate
     */
    extractZeroCrossingRate(audioData) {
        let crossings = 0;
        for (let i = 1; i < audioData.length; i++) {
            if ((audioData[i] >= 0 && audioData[i - 1] < 0) ||
                (audioData[i] < 0 && audioData[i - 1] >= 0)) {
                crossings++;
            }
        }
        return crossings / audioData.length;
    }

    /**
     * Extract energy distribution across frequency bands
     */
    extractEnergyDistribution(audioData) {
        const spectrum = this.computeSpectrum(audioData);
        const numBands = 8;
        const bandSize = Math.floor(spectrum.length / numBands);
        const energy = new Array(numBands).fill(0);

        for (let band = 0; band < numBands; band++) {
            const start = band * bandSize;
            const end = Math.min((band + 1) * bandSize, spectrum.length);

            for (let i = start; i < end; i++) {
                energy[band] += spectrum[i] * spectrum[i];
            }
        }

        // Normalize
        const totalEnergy = energy.reduce((sum, e) => sum + e, 0);
        if (totalEnergy > 0) {
            for (let i = 0; i < energy.length; i++) {
                energy[i] /= totalEnergy;
            }
        }

        return energy;
    }

    /**
     * Compute magnitude spectrum using FFT
     */
    computeSpectrum(audioData) {
        // Pad or truncate to fftSize
        const fftInput = new Float32Array(this.fftSize);
        const len = Math.min(audioData.length, this.fftSize);
        fftInput.set(audioData.subarray(0, len));

        // Apply Hamming window
        for (let i = 0; i < len; i++) {
            fftInput[i] *= 0.54 - 0.46 * Math.cos(2 * Math.PI * i / (len - 1));
        }

        // Simple DFT (for small sizes, FFT would be better but more complex)
        const spectrum = new Float32Array(this.fftSize / 2);

        for (let k = 0; k < this.fftSize / 2; k++) {
            let real = 0;
            let imag = 0;

            for (let n = 0; n < this.fftSize; n++) {
                const angle = -2 * Math.PI * k * n / this.fftSize;
                real += fftInput[n] * Math.cos(angle);
                imag += fftInput[n] * Math.sin(angle);
            }

            spectrum[k] = Math.sqrt(real * real + imag * imag);
        }

        return spectrum;
    }

    /**
     * Compare two feature vectors
     * @returns {number} Similarity score (0-1, higher is more similar)
     */
    compareFeatures(features1, features2) {
        if (!features1 || !features2) return 0;

        // Weighted feature comparison
        const weights = {
            f0: 0.3,
            spectralCentroid: 0.2,
            zcr: 0.1,
            energy: 0.4
        };

        let totalSimilarity = 0;

        // F0 similarity (inverse of normalized difference)
        const f0Diff = Math.abs(features1.f0 - features2.f0);
        const f0Max = Math.max(features1.f0, features2.f0, 1);
        const f0Sim = 1 - Math.min(f0Diff / f0Max, 1);
        totalSimilarity += f0Sim * weights.f0;

        // Spectral centroid similarity
        const scDiff = Math.abs(features1.spectralCentroid - features2.spectralCentroid);
        const scMax = Math.max(features1.spectralCentroid, features2.spectralCentroid, 1);
        const scSim = 1 - Math.min(scDiff / scMax, 1);
        totalSimilarity += scSim * weights.spectralCentroid;

        // ZCR similarity
        const zcrDiff = Math.abs(features1.zcr - features2.zcr);
        const zcrSim = 1 - Math.min(zcrDiff, 1);
        totalSimilarity += zcrSim * weights.zcr;

        // Energy distribution similarity (cosine similarity)
        const energySim = this.cosineSimilarity(features1.energy, features2.energy);
        totalSimilarity += energySim * weights.energy;

        return totalSimilarity;
    }

    /**
     * Compute cosine similarity between two vectors
     */
    cosineSimilarity(vec1, vec2) {
        if (vec1.length !== vec2.length) return 0;

        let dotProduct = 0;
        let norm1 = 0;
        let norm2 = 0;

        for (let i = 0; i < vec1.length; i++) {
            dotProduct += vec1[i] * vec2[i];
            norm1 += vec1[i] * vec1[i];
            norm2 += vec2[i] * vec2[i];
        }

        norm1 = Math.sqrt(norm1);
        norm2 = Math.sqrt(norm2);

        if (norm1 === 0 || norm2 === 0) return 0;

        return dotProduct / (norm1 * norm2);
    }
}

/**
 * Speaker Verifier using client-side fingerprinting
 */
class ClientSpeakerVerifier {
    constructor(threshold = 0.75) {
        this.threshold = threshold;
        this.fingerprinter = new VoiceFingerprint();
        this.enrolledFeatures = null;
        this.enrolled = false;
    }

    /**
     * Enroll speaker from audio samples
     */
    enroll(audioData) {
        const features = this.fingerprinter.extractFeatures(audioData);

        if (!features) {
            return { success: false, message: 'Audio too short for enrollment' };
        }

        this.enrolledFeatures = features;
        this.enrolled = true;

        console.log('[Speaker] Enrolled:', {
            f0: features.f0.toFixed(1),
            spectralCentroid: features.spectralCentroid.toFixed(1),
            zcr: features.zcr.toFixed(4)
        });

        return { success: true, message: 'Speaker enrolled successfully' };
    }

    /**
     * Verify if audio matches enrolled speaker
     */
    verify(audioData) {
        if (!this.enrolled) {
            return { isMatch: true, similarity: 1.0 }; // No enrollment, accept all
        }

        const features = this.fingerprinter.extractFeatures(audioData);

        if (!features) {
            return { isMatch: false, similarity: 0.0 }; // Too short
        }

        const similarity = this.fingerprinter.compareFeatures(
            this.enrolledFeatures,
            features
        );

        const isMatch = similarity >= this.threshold;

        return { isMatch, similarity };
    }

    /**
     * Reset enrollment
     */
    reset() {
        this.enrolledFeatures = null;
        this.enrolled = false;
    }

    /**
     * Check if speaker is enrolled
     */
    isEnrolled() {
        return this.enrolled;
    }

    /**
     * Get/set threshold
     */
    getThreshold() {
        return this.threshold;
    }

    setThreshold(threshold) {
        this.threshold = threshold;
    }
}

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VoiceFingerprint, ClientSpeakerVerifier };
}
