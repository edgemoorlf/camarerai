#!/usr/bin/env python3
"""
Real Performance Test Runner

Runs actual performance tests against real APIs using your .env credentials.
Automatically starts/stops servers and generates comparison reports.

Usage:
    python tests/run_real_performance_tests.py

Environment (auto-loaded from .env):
    DASHSCOPE_API_KEY - Required for dashscope provider
    GEMINI_API_KEY - Required for gemini and gemini_live providers
"""

import subprocess
import json
import time
import os
import sys
import signal
import glob
import urllib.request
import threading
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Load .env file
def load_env():
    """Load environment variables from .env file"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()


class RealTestRunner:
    """Runs real performance tests against actual APIs"""

    def __init__(self, iterations: int = 5, server_timeout: int = 60):
        self.iterations = iterations
        self.server_timeout = server_timeout
        self.results: Dict[str, Optional[Dict]] = {}
        self.server_process = None
        self.project_root = os.path.dirname(os.path.dirname(__file__))

    def check_api_key(self, provider: str) -> bool:
        """Check if required API key is available"""
        if provider == 'dashscope':
            if not os.getenv('DASHSCOPE_API_KEY'):
                print(f"❌ DASHSCOPE_API_KEY not found in .env")
                return False
            print(f"✓ DASHSCOPE_API_KEY found")
            return True
        else:  # gemini or gemini_live
            if not os.getenv('GEMINI_API_KEY'):
                print(f"❌ GEMINI_API_KEY not found in .env (required for {provider})")
                return False
            print(f"✓ GEMINI_API_KEY found")
            return True

    def start_server(self, provider: str) -> bool:
        """Start the voice agent server"""
        print(f"\n[Server] Starting {provider}...")

        env = os.environ.copy()
        env['PROVIDER'] = provider

        try:
            self.server_process = subprocess.Popen(
                [sys.executable, 'main.py'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root
            )

            # Wait for server to be ready
            start_time = time.time()
            while time.time() - start_time < self.server_timeout:
                try:
                    urllib.request.urlopen('http://localhost:5002', timeout=2)
                    print(f"✓ Server ready on http://localhost:5002")
                    return True
                except:
                    # Check if process crashed
                    if self.server_process.poll() is not None:
                        stdout, stderr = self.server_process.communicate()
                        print(f"❌ Server failed to start:")
                        if stderr:
                            print(stderr.decode())
                        if stdout:
                            print(stdout.decode())
                        return False
                    time.sleep(1)

            print(f"❌ Timeout waiting for server")
            return False

        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False

    def stop_server(self):
        """Stop the running server"""
        if self.server_process:
            try:
                self.server_process.send_signal(signal.SIGTERM)
                self.server_process.wait(timeout=5)
                print(f"✓ Server stopped")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                print(f"✓ Server killed")
            except Exception as e:
                print(f"⚠ Error stopping server: {e}")
            finally:
                self.server_process = None

    def run_scenario(self, provider: str, scenario: str, audio_file: str) -> Optional[Dict]:
        """Run a single test scenario and collect metrics using text-based chat instead of audio"""
        import socketio
        import base64

        sio = socketio.Client()
        metrics = {
            'scenario': scenario,
            'provider': provider,
            'timestamp': datetime.now().isoformat(),
            'events': {},
            'errors': []
        }

        session_id = None
        response_complete = False

        # Set up event handlers that use threading events
        session_event = threading.Event()
        response_event = threading.Event()

        # Map scenario names to test text
        scenario_texts = {
            'simple_order': "I'd like Kung Pao Chicken",
            'complex_order': "I want two orders of Dan Dan Noodles, one with extra spicy",
            'question': "What do you recommend?",
            'modification': "Actually, make that three instead",
            'greeting': "Hello, I'd like to place an order",
            'closing': "Thank you, that's all"
        }

        @sio.on('session_started')
        def on_session(data):
            nonlocal session_id
            session_id = data.get('session_id')
            metrics['events']['session_started'] = time.time()
            session_event.set()

        @sio.on('transcript')
        def on_transcript(data):
            if 'transcript' not in metrics['events']:
                metrics['events']['transcript'] = time.time()
                metrics['transcript_text'] = data.get('text', '')

        @sio.on('llm_started')
        def on_llm_started(data):
            metrics['events']['llm_started'] = time.time()

        @sio.on('llm_chunk')
        def on_llm_chunk(data):
            if 'llm_first_chunk' not in metrics['events']:
                metrics['events']['llm_first_chunk'] = time.time()

        @sio.on('synthesis_started')
        def on_tts_started(data):
            metrics['events']['tts_started'] = time.time()

        @sio.on('audio_chunk')
        def on_audio(data):
            nonlocal response_complete
            if data.get('is_final'):
                metrics['events']['audio_complete'] = time.time()
                response_complete = True
                # Don't set response_event here - we already set it on first audio
            elif 'first_audio' not in metrics['events']:
                metrics['events']['first_audio'] = time.time()
                # Set response received when we get first audio chunk
                response_event.set()

        @sio.on('error')
        def on_error(data):
            metrics['errors'].append(data.get('message', 'Unknown error'))
            response_event.set()  # Release wait on error

        try:
            sio.connect('http://localhost:5002', wait_timeout=10)
            metrics['events']['start'] = time.time()

            # Start session
            sio.emit('start_session', {'table_id': '1'})

            if not session_event.wait(timeout=5):
                raise Exception("Failed to create session - timeout")

            # Use text-based chat instead of audio (more reliable for testing)
            # This avoids ASR variability while still testing LLM+TTS latency
            test_text = scenario_texts.get(scenario, "Hello")

            metrics['events']['chat_sent'] = time.time()
            sio.emit('chat', {'session_id': session_id, 'message': test_text})

            # Wait for response (first audio chunk or timeout)
            if not response_event.wait(timeout=45):
                # Check if we at least got some events
                if 'tts_started' in metrics['events']:
                    metrics['errors'].append("TTS started but no audio chunks received")
                elif 'llm_started' in metrics['events']:
                    metrics['errors'].append("LLM started but TTS not started")
                else:
                    metrics['errors'].append("Timeout waiting for response")

            sio.disconnect()

            # Calculate metrics
            metrics['events']['end'] = time.time()
            metrics['duration'] = metrics['events']['end'] - metrics['events']['start']

            if 'llm_started' in metrics['events'] and 'llm_first_chunk' in metrics['events']:
                metrics['llm_first_token_ms'] = (
                    metrics['events']['llm_first_chunk'] - metrics['events']['llm_started']
                ) * 1000

            if 'tts_started' in metrics['events'] and 'first_audio' in metrics['events']:
                metrics['tts_first_audio_ms'] = (
                    metrics['events']['first_audio'] - metrics['events']['tts_started']
                ) * 1000

            # Total response = from chat sent to first audio (or synthesis_started as fallback)
            if 'chat_sent' in metrics['events']:
                if 'first_audio' in metrics['events']:
                    metrics['total_response_ms'] = (
                        metrics['events']['first_audio'] - metrics['events']['chat_sent']
                    ) * 1000
                elif 'tts_started' in metrics['events']:
                    # Fallback: use TTS start time if audio chunks not received
                    metrics['total_response_ms'] = (
                        metrics['events']['tts_started'] - metrics['events']['chat_sent']
                    ) * 1000

            return metrics

        except Exception as e:
            metrics['errors'].append(str(e))
            try:
                sio.disconnect()
            except:
                pass
            return metrics

    def run_scenario_audio(self, provider: str, scenario: str, audio_file: str) -> Optional[Dict]:
        """Run a single test scenario using audio input (for voice-only APIs like Gemini Live)"""
        import socketio
        import base64

        sio = socketio.Client()
        metrics = {
            'scenario': scenario,
            'provider': provider,
            'timestamp': datetime.now().isoformat(),
            'events': {},
            'errors': []
        }

        session_id = None
        response_complete = False

        # Set up event handlers that use threading events
        session_event = threading.Event()
        recognition_started_event = threading.Event()
        response_event = threading.Event()

        @sio.on('session_started')
        def on_session(data):
            nonlocal session_id
            session_id = data.get('session_id')
            metrics['events']['session_started'] = time.time()
            session_event.set()

        @sio.on('recognition_started')
        def on_recognition_started(data):
            metrics['events']['recognition_started'] = time.time()
            recognition_started_event.set()

        @sio.on('transcript')
        def on_transcript(data):
            if 'transcript' not in metrics['events']:
                metrics['events']['transcript'] = time.time()
                metrics['transcript_text'] = data.get('text', '')

        @sio.on('synthesis_started')
        def on_tts_started(data):
            metrics['events']['tts_started'] = time.time()

        @sio.on('audio_chunk')
        def on_audio(data):
            nonlocal response_complete
            if data.get('is_final'):
                metrics['events']['audio_complete'] = time.time()
                response_complete = True
            elif 'first_audio' not in metrics['events']:
                metrics['events']['first_audio'] = time.time()
                response_event.set()

        @sio.on('error')
        def on_error(data):
            metrics['errors'].append(data.get('message', 'Unknown error'))
            response_event.set()
            recognition_started_event.set()

        try:
            sio.connect('http://localhost:5002', wait_timeout=10)
            metrics['events']['start'] = time.time()

            # Start session
            sio.emit('start_session', {'table_id': '1'})

            if not session_event.wait(timeout=5):
                raise Exception("Failed to create session - timeout")

            # Start recognition (for audio-based APIs)
            sio.emit('start_recognition', {'session_id': session_id})

            if not recognition_started_event.wait(timeout=5):
                raise Exception("Failed to start recognition - timeout")

            # Brief wait for connection to stabilize
            time.sleep(0.5)

            # Read and stream audio file
            with open(audio_file, 'rb') as f:
                audio_data = f.read()

            # Stream audio in chunks (3200 bytes = 100ms at 16kHz 16-bit)
            chunk_size = 3200
            metrics['events']['audio_stream_start'] = time.time()

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                audio_b64 = base64.b64encode(chunk).decode('utf-8')
                sio.emit('audio_data', {'session_id': session_id, 'audio': audio_b64})

                # Check for early response after each chunk (for fast LLMs like Gemini)
                if response_event.is_set():
                    break

                time.sleep(0.1)  # Simulate real-time streaming

            metrics['events']['audio_stream_end'] = time.time()

            # Wait for response BEFORE stopping recognition
            if not response_event.wait(timeout=45):
                if 'tts_started' in metrics['events']:
                    metrics['errors'].append("TTS started but no audio chunks received")
                elif 'transcript' in metrics['events']:
                    metrics['errors'].append("Got transcript but no audio response")
                else:
                    metrics['errors'].append("Timeout waiting for response")

            # Stop recognition after getting response (or timeout)
            sio.emit('stop_recognition', {'session_id': session_id})
            sio.disconnect()

            # Calculate metrics
            metrics['events']['end'] = time.time()
            metrics['duration'] = metrics['events']['end'] - metrics['events']['start']

            if 'tts_started' in metrics['events'] and 'first_audio' in metrics['events']:
                metrics['tts_first_audio_ms'] = (
                    metrics['events']['first_audio'] - metrics['events']['tts_started']
                ) * 1000

            # Total response = from audio stream start to first audio (for streaming APIs)
            # This measures the latency from when user starts speaking to hearing response
            if 'audio_stream_start' in metrics['events']:
                if 'first_audio' in metrics['events']:
                    metrics['total_response_ms'] = (
                        metrics['events']['first_audio'] - metrics['events']['audio_stream_start']
                    ) * 1000
                elif 'tts_started' in metrics['events']:
                    metrics['total_response_ms'] = (
                        metrics['events']['tts_started'] - metrics['events']['audio_stream_start']
                    ) * 1000

            return metrics

        except Exception as e:
            metrics['errors'].append(str(e))
            try:
                sio.disconnect()
            except:
                pass
            return metrics

    def test_provider(self, provider: str) -> Optional[Dict]:
        """Run all tests for a provider"""
        print(f"\n{'='*70}")
        print(f"TESTING PROVIDER: {provider.upper()}")
        print(f"{'='*70}")

        # Check API key
        if not self.check_api_key(provider):
            return None

        # Start server
        if not self.start_server(provider):
            return None

        # Wait for initialization
        print(f"\n[Init] Waiting 3 seconds for warmup...")
        time.sleep(3)

        # Discover test scenarios
        fixtures_dir = os.path.join(self.project_root, 'tests', 'fixtures')
        scenarios = []
        for f in os.listdir(fixtures_dir):
            if f.endswith('.pcm'):
                scenarios.append(f.replace('.pcm', ''))

        print(f"\n[Tests] Running {len(scenarios)} scenarios x {self.iterations} iterations")
        print(f"Total API calls: ~{len(scenarios) * self.iterations}")
        print()

        results = []

        try:
            # Use audio-based testing for gemini_live (voice-only API)
            use_audio = (provider == 'gemini_live')

            for scenario in sorted(scenarios):
                audio_file = os.path.join(fixtures_dir, f"{scenario}.pcm")

                for i in range(self.iterations):
                    print(f"  {scenario} ({i+1}/{self.iterations})...", end=' ', flush=True)

                    if use_audio:
                        result = self.run_scenario_audio(provider, scenario, audio_file)
                    else:
                        result = self.run_scenario(provider, scenario, audio_file)
                    results.append(result)

                    if result.get('errors'):
                        error_msg = result['errors'][-1]
                        if 'total_response_ms' in result:
                            print(f"✓ {result['total_response_ms']:.0f}ms ({error_msg[:30]})")
                        else:
                            print(f"❌ {error_msg[:50]}")
                    elif 'total_response_ms' in result:
                        print(f"✓ {result['total_response_ms']:.0f}ms")
                    else:
                        print(f"⚠ Incomplete (no events: {list(result['events'].keys())})")

                    # Brief pause between tests
                    time.sleep(0.5)

        finally:
            # Always stop server
            self.stop_server()
            time.sleep(2)

        # Generate report
        return self._generate_report(results)

    def _generate_report(self, results: List[Dict]) -> Dict:
        """Generate summary report"""
        import statistics

        report = {
            'timestamp': datetime.now().isoformat(),
            'provider': self.provider if hasattr(self, 'provider') else 'unknown',
            'total_tests': len(results),
            'successful_tests': len([r for r in results if not r.get('errors') and 'total_response_ms' in r]),
            'summary': {},
            'details': results
        }

        metrics = ['llm_first_token_ms', 'tts_first_audio_ms', 'total_response_ms', 'transcription_latency_ms']

        for key in metrics:
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

    def run_all(self, providers: List[str] = None) -> Dict:
        """Run tests for all providers"""
        if providers is None:
            providers = ['dashscope', 'gemini', 'gemini_live']

        for provider in providers:
            self.results[provider] = self.test_provider(provider)

        return self._generate_comparison()

    def _generate_comparison(self) -> Dict:
        """Generate comparison across all providers"""
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'iterations': self.iterations,
            'providers': {},
            'comparison': {}
        }

        for provider, result in self.results.items():
            if result:
                comparison['providers'][provider] = result.get('summary', {})

        # Compare each metric
        metrics = ['llm_first_token_ms', 'tts_first_audio_ms', 'total_response_ms', 'transcription_latency_ms']
        for metric in metrics:
            metric_comparison = {}
            for provider, summary in comparison['providers'].items():
                if metric in summary:
                    metric_comparison[provider] = summary[metric]
            if metric_comparison:
                comparison['comparison'][metric] = metric_comparison

        return comparison

    def save_reports(self, comparison: Dict):
        """Save all reports"""
        reports_dir = os.path.join(self.project_root, 'tests', 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = int(time.time())

        # Save individual provider reports
        for provider, result in self.results.items():
            if result:
                filepath = os.path.join(reports_dir, f"perf_report_{provider}_{timestamp}.json")
                with open(filepath, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"\n📄 {provider} report: {filepath}")

        # Save comparison
        comparison_path = os.path.join(reports_dir, f"comparison_{timestamp}.json")
        with open(comparison_path, 'w') as f:
            json.dump(comparison, f, indent=2)
        print(f"📄 Comparison report: {comparison_path}")

        return comparison_path

    def print_comparison(self, comparison: Dict):
        """Print comparison table"""
        print("\n" + "="*70)
        print("PROVIDER COMPARISON")
        print("="*70)

        targets = {
            'llm_first_token_ms': 300,
            'tts_first_audio_ms': 200,
            'total_response_ms': 600
        }

        for metric, providers in comparison['comparison'].items():
            metric_name = metric.replace('_ms', '').replace('_', ' ').title()
            target = targets.get(metric)

            print(f"\n{metric_name}" + (f" (target: {target}ms)" if target else ""))
            print("-"*70)
            print(f"{'Provider':<15} {'Avg':<10} {'Min':<10} {'Max':<10} {'P95':<10} {'Status':<10}")
            print("-"*70)

            sorted_providers = sorted(providers.items(), key=lambda x: x[1].get('avg', float('inf')))

            for provider, stats in sorted_providers:
                avg = stats.get('avg', 0)
                if target:
                    status = "✅" if avg <= target else "❌"
                else:
                    status = "✓"

                marker = "★" if avg == sorted_providers[0][1].get('avg') else " "
                print(f"{marker}{provider:<14} "
                      f"{avg:<10.0f} "
                      f"{stats.get('min', 0):<10.0f} "
                      f"{stats.get('max', 0):<10.0f} "
                      f"{stats.get('p95', 0):<10.0f} "
                      f"{status}")

        # Overall winner
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)

        wins = {}
        for metric, providers in comparison['comparison'].items():
            if providers:
                winner = min(providers.items(), key=lambda x: x[1].get('avg', float('inf')))
                wins[winner[0]] = wins.get(winner[0], 0) + 1

        if wins:
            overall = max(wins.items(), key=lambda x: x[1])
            print(f"🏆 Best Overall: {overall[0]} ({overall[1]}/{len(comparison['comparison'])} metrics)")
            print()

            for provider, count in sorted(wins.items(), key=lambda x: -x[1]):
                print(f"  {provider}: {count} fastest metrics")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Run real performance tests')
    parser.add_argument('--iterations', '-i', type=int, default=5,
                        help='Iterations per scenario (default: 5)')
    parser.add_argument('--providers', '-p', nargs='+',
                        choices=['dashscope', 'gemini', 'gemini_live'],
                        default=['dashscope', 'gemini', 'gemini_live'],
                        help='Providers to test (default: all)')
    parser.add_argument('--timeout', '-t', type=int, default=60,
                        help='Server startup timeout (default: 60s)')

    args = parser.parse_args()

    print("="*70)
    print("REAL PERFORMANCE TEST RUNNER")
    print("="*70)
    print(f"Providers: {', '.join(args.providers)}")
    print(f"Iterations: {args.iterations}")
    print(f"Scenarios: 6 (simple_order, complex_order, question, modification, greeting, closing)")
    print(f"Total API calls: ~{len(args.providers) * 6 * args.iterations}")
    print()
    print("⚠️  This will make REAL API calls and incur costs!")
    print("   Press Ctrl+C within 3 seconds to cancel...")
    print()

    time.sleep(3)

    runner = RealTestRunner(
        iterations=args.iterations,
        server_timeout=args.timeout
    )

    try:
        comparison = runner.run_all(args.providers)
        runner.print_comparison(comparison)
        runner.save_reports(comparison)

        print("\n" + "="*70)
        print("TESTING COMPLETE")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        runner.stop_server()
        sys.exit(1)


if __name__ == '__main__':
    main()
