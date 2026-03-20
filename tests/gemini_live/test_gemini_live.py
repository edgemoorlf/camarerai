#!/usr/bin/env python3
"""
Gemini Live Provider Tests
Tests for Gemini Live API (native bidirectional audio streaming)
"""

import subprocess
import json
import time
import os
import sys
import threading
import base64
from pathlib import Path
from typing import Dict, List, Optional

# Load .env file
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()


class GeminiLiveTester:
    """Test runner for Gemini Live provider"""

    def __init__(self, iterations: int = 3):
        self.iterations = iterations
        self.project_root = os.path.join(os.path.dirname(__file__), '..')
        self.server_process = None
        self.audio_dir = os.path.join(self.project_root, 'tests', 'fixtures')

    def check_api_key(self) -> bool:
        """Check if required API key is available"""
        if not os.getenv('GEMINI_API_KEY'):
            print("❌ GEMINI_API_KEY not found in .env")
            return False
        print(f"✓ GEMINI_API_KEY found")
        return True

    def start_server(self) -> bool:
        """Start the Gemini Live voice agent server"""
        env = os.environ.copy()
        env['PROVIDER'] = 'gemini_live'
        env['PORT'] = '5002'

        cmd = [sys.executable, 'main.py']
        self.server_process = subprocess.Popen(
            cmd,
            cwd=self.project_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        for _ in range(30):
            try:
                import urllib.request
                urllib.request.urlopen('http://localhost:5002', timeout=1)
                print(f"✓ Server ready on http://localhost:5002")
                return True
            except:
                time.sleep(0.5)

        print("❌ Server failed to start")
        return False

    def stop_server(self):
        """Stop the server"""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
            print("✓ Server stopped")

    def run_test(self, scenario: str) -> Optional[Dict]:
        """Run a single test scenario using audio input"""
        import socketio

        sio = socketio.Client()
        metrics = {'scenario': scenario, 'events': {}, 'errors': []}

        session_id = None
        response_event = threading.Event()

        @sio.on('session_started')
        def on_session(data):
            nonlocal session_id
            session_id = data.get('session_id')
            metrics['events']['session_started'] = time.time()

        @sio.on('recognition_started')
        def on_recognition_started(data):
            metrics['events']['recognition_started'] = time.time()

        @sio.on('audio_chunk')
        def on_audio(data):
            if 'first_audio' not in metrics['events'] and not data.get('is_final'):
                metrics['events']['first_audio'] = time.time()
                response_event.set()
            if data.get('is_final'):
                response_event.set()

        @sio.on('error')
        def on_error(data):
            metrics['errors'].append(data.get('message', 'Unknown error'))
            response_event.set()

        try:
            sio.connect('http://localhost:5002', wait_timeout=10)
            metrics['events']['start'] = time.time()

            sio.emit('start_session', {'table_id': '1'})
            time.sleep(0.5)

            sio.emit('start_recognition', {'session_id': session_id})
            time.sleep(1)

            audio_file = os.path.join(self.audio_dir, f"{scenario}.pcm")
            if not os.path.exists(audio_file):
                audio_file = os.path.join(self.audio_dir, "simple_order.pcm")

            with open(audio_file, 'rb') as f:
                audio_data = f.read()

            chunk_size = 3200
            metrics['events']['audio_stream_start'] = time.time()

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                audio_b64 = base64.b64encode(chunk).decode('utf-8')
                sio.emit('audio_data', {'session_id': session_id, 'audio': audio_b64})

                if response_event.is_set():
                    break
                time.sleep(0.1)

            metrics['events']['audio_stream_end'] = time.time()

            if not response_event.wait(timeout=30):
                metrics['errors'].append("Timeout")

            sio.emit('stop_recognition', {'session_id': session_id})
            sio.disconnect()

            if 'first_audio' in metrics['events']:
                metrics['total_response_ms'] = (
                    metrics['events']['first_audio'] - metrics['events']['audio_stream_start']
                ) * 1000

            return metrics

        except Exception as e:
            metrics['errors'].append(str(e))
            return metrics

    def run_all(self) -> Dict:
        """Run all tests"""
        print("\n" + "=" * 60)
        print("GEMINI LIVE PROVIDER TESTS")
        print("=" * 60)

        if not self.check_api_key():
            return {'error': 'API key not found'}

        if not self.start_server():
            return {'error': 'Server failed to start'}

        time.sleep(2)

        scenarios = ['simple_order', 'complex_order', 'question', 'modification', 'greeting', 'closing']
        results = []

        for scenario in scenarios:
            for i in range(self.iterations):
                print(f"  {scenario} ({i+1}/{self.iterations})...", end=' ', flush=True)
                result = self.run_test(scenario)
                if result.get('total_response_ms'):
                    print(f"✓ {result['total_response_ms']:.0f}ms")
                else:
                    print(f"❌ {result.get('errors', ['Unknown'])[0]}")
                results.append(result)

        self.stop_server()

        successes = [r for r in results if 'total_response_ms' in r]
        if successes:
            avg_time = sum(r['total_response_ms'] for r in successes) / len(successes)
            print(f"\n✓ {len(successes)}/{len(results)} tests passed")
            print(f"  Average response time: {avg_time:.0f}ms")

        return {
            'provider': 'gemini_live',
            'results': results,
            'passed': len(successes),
            'total': len(results)
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Test Gemini Live Provider')
    parser.add_argument('-i', '--iterations', type=int, default=1, help='Iterations per scenario')
    args = parser.parse_args()

    tester = GeminiLiveTester(iterations=args.iterations)
    results = tester.run_all()

    report_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"test_gemini_live_{int(time.time())}.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Report saved: {report_path}")

    return 0 if results.get('passed', 0) == results.get('total', 0) else 1


if __name__ == '__main__':
    sys.exit(main())
