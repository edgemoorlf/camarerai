"""
Performance Monitoring Module
Tracks response time metrics for ASR, LLM, and TTS
"""

import time
from datetime import datetime
from collections import deque


class PerformanceMetrics:
    """Track and analyze performance metrics"""

    def __init__(self, max_history=100):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.current_request = {}

    def start_timer(self, stage):
        """Start timing a stage"""
        self.current_request[f'{stage}_start'] = time.time()
        print(f"[Perf] {stage} started at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

    def end_timer(self, stage):
        """End timing a stage and return duration in ms"""
        start_time = self.current_request.get(f'{stage}_start')
        if start_time:
            duration_ms = (time.time() - start_time) * 1000
            self.current_request[f'{stage}_duration'] = duration_ms
            print(f"[Perf] {stage} completed in {duration_ms:.0f}ms")
            return duration_ms
        return None

    def mark_event(self, event_name):
        """Mark a specific event timestamp"""
        self.current_request[event_name] = time.time()
        print(f"[Perf] {event_name} at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

    def calculate_duration(self, start_event, end_event):
        """Calculate duration between two events"""
        start_time = self.current_request.get(start_event)
        end_time = self.current_request.get(end_event)
        if start_time and end_time:
            duration_ms = (end_time - start_time) * 1000
            return duration_ms
        return None

    def record_request(self):
        """Save current request metrics and reset"""
        if self.current_request:
            # Calculate derived metrics
            self._calculate_derived_metrics()

            # Add timestamp
            self.current_request['timestamp'] = datetime.now().isoformat()

            # Save to history
            self.metrics_history.append(self.current_request.copy())

            # Log summary
            self._log_request_summary()

            # Reset for next request
            self.current_request = {}

    def _calculate_derived_metrics(self):
        """Calculate derived metrics from raw timings"""
        # Total response time (speech end to first audio)
        if 'asr_complete' in self.current_request and 'first_audio' in self.current_request:
            total = self.calculate_duration('asr_complete', 'first_audio')
            if total:
                self.current_request['total_response_time'] = total

        # LLM first token time
        if 'llm_start' in self.current_request and 'llm_first_chunk' in self.current_request:
            llm_first = self.calculate_duration('llm_start', 'llm_first_chunk')
            if llm_first:
                self.current_request['llm_first_token'] = llm_first

        # TTS first audio time
        if 'tts_start' in self.current_request and 'first_audio' in self.current_request:
            tts_first = self.calculate_duration('tts_start', 'first_audio')
            if tts_first:
                self.current_request['tts_first_audio'] = tts_first

    def _log_request_summary(self):
        """Log a summary of the current request"""
        metrics = self.current_request
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)

        if 'asr_duration' in metrics:
            print(f"ASR Duration:        {metrics['asr_duration']:.0f}ms")

        if 'llm_first_token' in metrics:
            print(f"LLM First Token:     {metrics['llm_first_token']:.0f}ms")

        if 'llm_duration' in metrics:
            print(f"LLM Total:           {metrics['llm_duration']:.0f}ms")

        if 'tts_first_audio' in metrics:
            print(f"TTS First Audio:     {metrics['tts_first_audio']:.0f}ms")

        if 'total_response_time' in metrics:
            print(f"Total Response Time: {metrics['total_response_time']:.0f}ms")
            print("-"*60)
            if metrics['total_response_time'] < 2000:
                print("✅ EXCELLENT - Under 2 seconds!")
            elif metrics['total_response_time'] < 3000:
                print("✓ GOOD - Under 3 seconds")
            else:
                print("⚠️  SLOW - Over 3 seconds")

        print("="*60 + "\n")

    def get_statistics(self):
        """Get statistical summary of all metrics"""
        if not self.metrics_history:
            return {}

        stats = {}
        metric_keys = [
            'asr_duration',
            'llm_first_token',
            'llm_duration',
            'tts_first_audio',
            'total_response_time'
        ]

        for key in metric_keys:
            values = [m.get(key) for m in self.metrics_history if m.get(key) is not None]
            if values:
                stats[key] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values),
                    'latest': values[-1] if values else None
                }

        return stats

    def print_statistics(self):
        """Print statistical summary"""
        stats = self.get_statistics()
        if not stats:
            print("[Perf] No metrics collected yet")
            return

        print("\n" + "="*60)
        print("PERFORMANCE STATISTICS")
        print(f"Based on {len(self.metrics_history)} requests")
        print("="*60)

        for metric_name, metric_stats in stats.items():
            display_name = metric_name.replace('_', ' ').title()
            print(f"\n{display_name}:")
            print(f"  Average: {metric_stats['avg']:.0f}ms")
            print(f"  Min:     {metric_stats['min']:.0f}ms")
            print(f"  Max:     {metric_stats['max']:.0f}ms")
            print(f"  Latest:  {metric_stats['latest']:.0f}ms")

        print("="*60 + "\n")

    def get_metrics_for_client(self):
        """Get metrics formatted for client display"""
        stats = self.get_statistics()
        latest = self.metrics_history[-1] if self.metrics_history else {}

        return {
            'current': {
                'asr': latest.get('asr_duration'),
                'llm_first_token': latest.get('llm_first_token'),
                'tts_first_audio': latest.get('tts_first_audio'),
                'total': latest.get('total_response_time')
            },
            'statistics': stats,
            'request_count': len(self.metrics_history)
        }
