"""
Automated Performance Test Runner

Runs performance tests against a running voice agent server.
Captures timing metrics via WebSocket events.

Usage:
    python tests/performance/run_performance_tests.py [provider]

Environment:
    PROVIDER - Provider to test (dashscope, gemini, gemini_live)
    SERVER_URL - Server URL (default: http://localhost:5002)
"""

import asyncio
import json
import time
import statistics
import os
import sys
import base64
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Note: python-socketio is required
try:
    import socketio
    import aiohttp
except ImportError:
    print("Error: Required packages not installed")
    print("Install with: pip install python-socketio aiohttp")
    sys.exit(1)


class PerformanceTestRunner:
    """Runs automated performance tests via WebSocket"""

    def __init__(self, provider: str = 'dashscope', base_url: str = 'http://localhost:5002'):
        self.provider = provider
        self.base_url = base_url
        self.results: List[Dict] = []
        self.fixtures_dir = 'tests/fixtures'
        self.reports_dir = 'tests/reports'

        os.makedirs(self.reports_dir, exist_ok=True)

    async def run_single_test(self, scenario_name: str, audio_file: str,
                              timeout: int = 30) -> Optional[Dict]:
        """
        Run a single performance test scenario

        Args:
            scenario_name: Name of the test scenario
            audio_file: Path to PCM audio file
            timeout: Maximum test duration in seconds

        Returns:
            Dict with metrics or None if test failed
        """
        metrics = {
            'scenario': scenario_name,
            'provider': self.provider,
            'timestamp': datetime.now().isoformat(),
            'events': {},
            'errors': []
        }

        sio = socketio.AsyncClient()
        session_id = None
        test_complete = asyncio.Event()

        @sio.on('connect')
        async def on_connect():
            metrics['events']['connected'] = time.time()

        @sio.on('session_started')
        async def on_session_started(data):
            nonlocal session_id
            session_id = data.get('session_id')
            metrics['events']['session_started'] = time.time()
            metrics['session_id'] = session_id

        @sio.on('recognition_started')
        async def on_recognition_started(data):
            metrics['events']['recognition_started'] = time.time()

        @sio.on('transcript')
        async def on_transcript(data):
            if 'transcript' not in metrics['events']:
                metrics['events']['transcript'] = time.time()
                metrics['transcript_text'] = data.get('text', '')

        @sio.on('llm_started')
        async def on_llm_started(data):
            metrics['events']['llm_started'] = time.time()

        @sio.on('llm_chunk')
        async def on_llm_chunk(data):
            if 'llm_first_chunk' not in metrics['events']:
                metrics['events']['llm_first_chunk'] = time.time()

        @sio.on('synthesis_started')
        async def on_synthesis_started(data):
            metrics['events']['tts_started'] = time.time()

        @sio.on('audio_chunk')
        async def on_audio_chunk(data):
            if data.get('is_final'):
                metrics['events']['audio_complete'] = time.time()
                test_complete.set()
            elif 'first_audio' not in metrics['events']:
                metrics['events']['first_audio'] = time.time()

        @sio.on('error')
        async def on_error(data):
            metrics['errors'].append({
                'time': time.time(),
                'message': data.get('message', 'Unknown error')
            })

        @sio.on('disconnect')
        async def on_disconnect():
            test_complete.set()

        try:
            # Connect to server
            await sio.connect(self.base_url, wait_timeout=10)
            metrics['events']['start'] = time.time()

            # Start session
            await sio.emit('start_session', {'table_id': '1'})
            await asyncio.wait_for(test_complete.wait(), timeout=2)
            test_complete.clear()

            if not session_id:
                raise Exception("Failed to create session")

            # Start recognition
            await sio.emit('start_recognition', {'session_id': session_id})
            await asyncio.wait_for(test_complete.wait(), timeout=2)
            test_complete.clear()

            # Stream audio in chunks
            with open(audio_file, 'rb') as f:
                audio_data = f.read()

            # 100ms chunks at 16kHz, 16-bit = 3200 bytes
            chunk_size = 3200
            chunk_duration = 0.1  # 100ms

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                await sio.emit('audio_data', {
                    'session_id': session_id,
                    'audio': base64.b64encode(chunk).decode('utf-8')
                })
                await asyncio.sleep(chunk_duration)

            # Stop recognition
            await sio.emit('stop_recognition', {'session_id': session_id})

            # Wait for completion (TTS playback)
            try:
                await asyncio.wait_for(test_complete.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                metrics['errors'].append({
                    'time': time.time(),
                    'message': 'Test timeout - audio did not complete'
                })

            await sio.disconnect()

            # Calculate derived metrics
            metrics['events']['end'] = time.time()
            metrics['duration'] = metrics['events']['end'] - metrics['events']['start']

            # LLM first token latency
            if 'llm_started' in metrics['events'] and 'llm_first_chunk' in metrics['events']:
                metrics['llm_first_token_ms'] = (
                    metrics['events']['llm_first_chunk'] -
                    metrics['events']['llm_started']
                ) * 1000

            # TTS first audio latency
            if 'tts_started' in metrics['events'] and 'first_audio' in metrics['events']:
                metrics['tts_first_audio_ms'] = (
                    metrics['events']['first_audio'] -
                    metrics['events']['tts_started']
                ) * 1000

            # Total response latency (speech end to first audio)
            if 'recognition_started' in metrics['events'] and 'first_audio' in metrics['events']:
                metrics['total_response_ms'] = (
                    metrics['events']['first_audio'] -
                    metrics['events']['recognition_started']
                ) * 1000

            # Transcription latency
            if 'recognition_started' in metrics['events'] and 'transcript' in metrics['events']:
                metrics['transcription_latency_ms'] = (
                    metrics['events']['transcript'] -
                    metrics['events']['recognition_started']
                ) * 1000

            return metrics

        except Exception as e:
            metrics['errors'].append({
                'time': time.time(),
                'message': str(e)
            })
            try:
                await sio.disconnect()
            except:
                pass
            return metrics

    async def run_all_tests(self, iterations: int = 5,
                            scenarios: Optional[List[str]] = None) -> Dict:
        """
        Run all test scenarios multiple times

        Args:
            iterations: Number of times to run each scenario
            scenarios: List of scenario names (default: all)

        Returns:
            Dict with full report including summary statistics
        """
        # Discover available scenarios
        if scenarios is None:
            scenarios = []
            for f in os.listdir(self.fixtures_dir):
                if f.endswith('.pcm'):
                    scenarios.append(f.replace('.pcm', ''))

        if not scenarios:
            print(f"No test fixtures found in {self.fixtures_dir}")
            print("Run: python tests/performance/test_audio_generator.py")
            return {}

        print(f"Running {len(scenarios)} scenarios x {iterations} iterations")
        print(f"Provider: {self.provider}")
        print(f"Server: {self.base_url}")
        print()

        all_results = []

        for scenario in sorted(scenarios):
            audio_file = os.path.join(self.fixtures_dir, f"{scenario}.pcm")

            if not os.path.exists(audio_file):
                print(f"  Skipping {scenario} - fixture not found")
                continue

            for i in range(iterations):
                print(f"  {scenario} (iteration {i + 1}/{iterations})...", end=' ')

                try:
                    result = await self.run_single_test(scenario, audio_file)
                    all_results.append(result)

                    if result.get('errors'):
                        print(f"FAILED - {result['errors'][-1]['message'][:50]}")
                    elif 'total_response_ms' in result:
                        print(f"OK - {result['total_response_ms']:.0f}ms")
                    else:
                        print("INCOMPLETE")

                except Exception as e:
                    print(f"ERROR - {e}")

        # Generate summary
        report = self._generate_report(all_results)
        return report

    def _generate_report(self, results: List[Dict]) -> Dict:
        """Generate summary report from test results"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'provider': self.provider,
            'total_tests': len(results),
            'successful_tests': len([r for r in results if not r.get('errors')]),
            'summary': {},
            'details': results
        }

        # Metrics to summarize
        metric_keys = [
            'llm_first_token_ms',
            'tts_first_audio_ms',
            'total_response_ms',
            'transcription_latency_ms'
        ]

        for key in metric_keys:
            values = [r[key] for r in results if key in r]
            if values:
                report['summary'][key] = {
                    'count': len(values),
                    'avg': statistics.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'median': statistics.median(values),
                    'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                    'p95': sorted(values)[int(len(values) * 0.95)] if len(values) >= 20 else max(values)
                }

        return report

    def save_report(self, report: Dict) -> str:
        """Save report to file and return path"""
        timestamp = int(time.time())
        filename = f"perf_report_{self.provider}_{timestamp}.json"
        filepath = os.path.join(self.reports_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        return filepath

    def print_summary(self, report: Dict):
        """Print report summary to console"""
        print()
        print("=" * 70)
        print(f"PERFORMANCE REPORT: {self.provider.upper()}")
        print("=" * 70)
        print()

        # Test summary
        total = report['total_tests']
        success = report['successful_tests']
        print(f"Tests: {success}/{total} successful")
        print()

        # Metrics table
        if report['summary']:
            print(f"{'Metric':<30} {'Avg':<10} {'Min':<10} {'Max':<10} {'P95':<10}")
            print("-" * 70)

            for metric, stats in report['summary'].items():
                metric_name = metric.replace('_ms', '').replace('_', ' ').title()
                print(f"{metric_name:<30} "
                      f"{stats['avg']:<10.0f} "
                      f"{stats['min']:<10.0f} "
                      f"{stats['max']:<10.0f} "
                      f"{stats['p95']:<10.0f}")

        print()

        # Target comparison
        targets = {
            'llm_first_token_ms': 300,
            'tts_first_audio_ms': 200,
            'total_response_ms': 600
        }

        print("TARGET COMPARISON:")
        print("-" * 70)
        for metric, target in targets.items():
            if metric in report['summary']:
                actual = report['summary'][metric]['avg']
                status = "✅" if actual <= target else "❌"
                print(f"  {status} {metric.replace('_ms', '').replace('_', ' ').title()}: "
                      f"{actual:.0f}ms (target: {target}ms)")

        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Run performance tests')
    parser.add_argument('provider', nargs='?',
                        default=os.getenv('PROVIDER', 'dashscope'),
                        help='Provider to test (dashscope, gemini, gemini_live)')
    parser.add_argument('--url', default='http://localhost:5002',
                        help='Server URL')
    parser.add_argument('--iterations', '-i', type=int, default=5,
                        help='Iterations per scenario')
    parser.add_argument('--scenarios', '-s', nargs='+',
                        help='Specific scenarios to run')

    args = parser.parse_args()

    # Check server is running
    import urllib.request
    try:
        urllib.request.urlopen(args.url, timeout=5)
    except:
        print(f"Error: Server not running at {args.url}")
        print("Start the server first:")
        print(f"  PROVIDER={args.provider} python main.py")
        sys.exit(1)

    # Run tests
    runner = PerformanceTestRunner(args.provider, args.url)

    asyncio.run(runner.run_all_tests(
        iterations=args.iterations,
        scenarios=args.scenarios
    ))

    # Report will be generated by the runner


if __name__ == '__main__':
    main()
