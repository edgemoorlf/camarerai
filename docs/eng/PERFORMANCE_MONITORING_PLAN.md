# Performance Monitoring Implementation Plan

## Objective
Build comprehensive performance monitoring to measure response metrics for ASR, LLM, and TTS with both real-time and statistical results.

## Metrics to Track

### 1. ASR Metrics
- **Time to first transcription**: From speech end to first ASR result
- **Transcription complete time**: Total ASR processing time

### 2. LLM Metrics
- **Time to first token**: From transcription complete to first LLM chunk
- **Time to complete**: Total LLM generation time
- **Tokens per second**: Generation speed

### 3. TTS Metrics
- **Time to first audio**: From LLM start to first audio chunk
- **Time to complete**: Total TTS synthesis time

### 4. End-to-End Metrics
- **Total response time**: From speech end to first audio playback
- **Pipeline efficiency**: Overlap between stages

## Implementation

### Backend (voice_agent.py)

```python
class PerformanceMetrics:
    def __init__(self):
        self.metrics = []
        self.current_request = {}

    def start_timer(self, stage):
        self.current_request[f'{stage}_start'] = time.time()

    def end_timer(self, stage):
        start_time = self.current_request.get(f'{stage}_start')
        if start_time:
            duration = (time.time() - start_time) * 1000  # ms
            self.current_request[f'{stage}_duration'] = duration
            return duration
        return None

    def record_request(self):
        self.metrics.append(self.current_request.copy())
        self.current_request = {}

    def get_statistics(self):
        if not self.metrics:
            return {}

        stats = {}
        for key in ['asr_duration', 'llm_first_token', 'tts_first_audio', 'total_duration']:
            values = [m.get(key) for m in self.metrics if m.get(key)]
            if values:
                stats[key] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        return stats
```

### Frontend (app.js)

```javascript
class PerformanceMonitor {
    constructor() {
        this.metrics = [];
        this.currentRequest = {};
    }

    startTimer(stage) {
        this.currentRequest[`${stage}_start`] = performance.now();
    }

    endTimer(stage) {
        const startTime = this.currentRequest[`${stage}_start`];
        if (startTime) {
            const duration = performance.now() - startTime;
            this.currentRequest[`${stage}_duration`] = duration;
            return duration;
        }
        return null;
    }

    recordRequest() {
        this.metrics.push({...this.currentRequest});
        this.updateUI();
        this.currentRequest = {};
    }

    updateUI() {
        // Update real-time metrics
        // Update statistics
    }
}
```

### UI Components

1. **Real-time Metrics Panel** (floating, top-right)
   - Current request metrics
   - Color-coded (green < 1s, yellow < 2s, red > 2s)

2. **Statistics Panel** (expandable)
   - Average response times
   - Min/Max values
   - Request count
   - Charts (optional)

## Timeline

1. **Phase 1**: Backend tracking (30 min)
2. **Phase 2**: Frontend tracking (30 min)
3. **Phase 3**: UI display (45 min)
4. **Phase 4**: Statistics and logging (30 min)

**Total**: ~2 hours

## Success Criteria

- ✅ Track all key metrics
- ✅ Display real-time metrics on UI
- ✅ Show statistical summaries
- ✅ Log to server with timestamps
- ✅ Validate streaming performance improvement
