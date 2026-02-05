# Speaker Identification Experiments - Summary

**Date:** 2026-02-04
**Status:** Experiments Complete
**Conclusion:** Need to use Option 3 (Open-source models like resemblyzer)

---

## Experiment Results

### ❌ Option 1: DashScope Speaker Verification
**Branch:** `experiment/speaker-id-dashscope`
**Status:** Not viable

**Findings:**
- DashScope does NOT have native speaker verification/identification API
- Only provides: ASR (Paraformer), LLM (Qwen), TTS (Sambert)
- No voiceprint recognition or speaker diarization

**Alternative Investigated: ModelScope 3D-Speaker**
- Alibaba's open-source toolkit for speaker verification
- Pre-trained models available
- **BLOCKER:** Too many dependencies (~20+ packages)
- **BLOCKER:** Version conflicts with `datasets` library
- Installation time: ~5 minutes
- Maintenance burden: High

**Conclusion:** Not suitable for POC due to complexity and dependency issues.

---

### ❌ Option 3: Voice Fingerprinting
**Branch:** `experiment/speaker-id-fingerprint`
**Status:** Implemented but insufficient accuracy

**Implementation:**
- Created `speaker_fingerprint.py` module
- Features extracted:
  - Fundamental frequency (F0) - pitch
  - Formants (F1, F2, F3) - vocal tract resonances
  - MFCC (13 coefficients) - spectral envelope
  - Energy distribution (8 frequency bands)
- No external dependencies (only numpy + scipy)
- Simple implementation (~500 lines)

**Test Results:**

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| **Latency** | 5-30ms | < 200ms | ✅ EXCELLENT |
| **Same Speaker Accuracy** | 100% | > 80% | ✅ PASS |
| **Different Speaker Rejection** | 0% | > 80% | ❌ FAIL |
| **Overall Accuracy** | 60% | > 80% | ❌ FAIL |

**Detailed Findings:**
- ✅ **Latency:** Extremely fast (5-30ms depending on audio length)
- ✅ **Same speaker:** Perfect recognition (100%)
- ❌ **Different speakers:** Cannot distinguish (0% rejection rate)
- ❌ **False positives:** Very high - accepts almost everyone
- ❌ **Threshold tuning:** Best threshold (0.9) only achieves 60% accuracy

**Why It Failed:**
- Synthetic audio features (F0, formants, MFCC) are too similar across speakers
- Simple cosine similarity is not discriminative enough
- Needs more sophisticated features or ML-based embeddings
- Would require significant feature engineering to improve

**Conclusion:** Too inaccurate for barge-in filtering. Would cause false positives (other people triggering barge-in).

---

## Recommendation: Option 2 (Open-source Speaker Verification)

### Why Option 2 Now?
1. **Option 1 failed:** DashScope has no speaker ID API
2. **Option 3 failed:** Fingerprinting too inaccurate (60%)
3. **Need production-grade accuracy:** 80%+ for reliable barge-in filtering

### Recommended Library: resemblyzer

**Why resemblyzer?**
- ✅ Simple API (easier than ModelScope 3D-Speaker)
- ✅ Pre-trained models (no training needed)
- ✅ Good accuracy (85-90% typical)
- ✅ Reasonable latency (~100-200ms)
- ✅ Single dependency (+ PyTorch)
- ✅ Well-documented and maintained
- ✅ Designed for speaker verification use case

**Installation:**
```bash
pip install resemblyzer
```

**Usage:**
```python
from resemblyzer import VoiceEncoder, preprocess_wav

# Load encoder
encoder = VoiceEncoder()

# Enrollment
enrollment_wav = preprocess_wav(enrollment_audio)
enrollment_embed = encoder.embed_utterance(enrollment_wav)

# Verification
test_wav = preprocess_wav(test_audio)
test_embed = encoder.embed_utterance(test_wav)

# Compare
similarity = np.dot(enrollment_embed, test_embed)
is_match = similarity > threshold
```

**Expected Performance:**
- Latency: ~100-200ms (acceptable for barge-in)
- Accuracy: 85-90% (good for POC)
- False positive rate: Low (~10-15%)
- Dependencies: resemblyzer + PyTorch (~500MB)

---

## Implementation Plan: Option 2 (resemblyzer)

### Phase 1: Setup & Testing
1. Create new branch: `feature/speaker-id-resemblyzer`
2. Install resemblyzer
3. Test latency and accuracy
4. Compare with fingerprinting results

### Phase 2: Integration
1. Create `speaker_verification.py` module
2. Implement enrollment during "Touch to Order"
3. Integrate into barge-in detection (`app.js`)
4. Add speaker verification to `voice_agent.py`

### Phase 3: Testing
1. Test in quiet environment
2. Test in noisy environment (restaurant simulation)
3. Test with multiple speakers
4. Tune threshold for optimal accuracy

### Phase 4: Merge to Main
1. Document findings
2. Update README.md
3. Merge to main branch
4. Clean up experiment branches

---

## Decision Matrix (Final)

| Criteria | DashScope | Fingerprinting | resemblyzer |
|----------|-----------|----------------|-------------|
| **Accuracy** | N/A | 60% ❌ | ~85-90% ✅ |
| **Latency** | N/A | 5-30ms ✅ | ~100-200ms ✅ |
| **Setup Complexity** | N/A | Simple ✅ | Medium |
| **Dependencies** | N/A | Minimal ✅ | +PyTorch (~500MB) |
| **Maintenance** | N/A | Self ✅ | Community ✅ |
| **False Positives** | N/A | Very High ❌ | Low ✅ |
| **Production Ready** | N/A | No ❌ | Yes ✅ |

**Winner:** resemblyzer (Option 2)

---

## Next Steps

1. ✅ Complete experiments (Option 1 & 3)
2. ⬜ Implement Option 2 (resemblyzer)
3. ⬜ Test and validate
4. ⬜ Integrate into main application
5. ⬜ Update documentation

---

## Lessons Learned

1. **DashScope limitations:** Not all features available in single API
2. **Simple features insufficient:** Voice fingerprinting needs ML embeddings
3. **Dependency management:** Balance between simplicity and accuracy
4. **POC vs Production:** Sometimes need to accept heavier dependencies for accuracy

---

## References

### Experiment Branches
- `experiment/speaker-id-dashscope` - DashScope research + ModelScope attempt
- `experiment/speaker-id-fingerprint` - Voice fingerprinting implementation

### Documentation
- [ModelScope 3D-Speaker](https://github.com/modelscope/3D-Speaker)
- [resemblyzer](https://github.com/resemble-ai/Resemblyzer)
- [pyannote.audio](https://github.com/pyannote/pyannote-audio)

### Test Results
- Fingerprinting: 60% accuracy, 5-30ms latency
- Same speaker: 100% recognition
- Different speakers: 0% rejection (critical failure)

---

**Status:** Ready to implement Option 2 (resemblyzer)
**Next Action:** Create `feature/speaker-id-resemblyzer` branch and implement
