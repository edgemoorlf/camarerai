#!/usr/bin/env python3
"""
Gemini Standard Provider Tests
Tests for Gemini Standard API (ASR + LLM) + DashScope TTS implementation
"""

import subprocess
import json
import time
import os
import sys
import threading
from datetime import datetime
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


class GeminiTester:
    """Test runner for Gemini Standard provider"""

    def __init__(self, iterations: int = 3):
        self.iterations = iterations
        self.project_root = os.path.join(os.path.dirname(__file__), '..')
        self.server_process = None

    def check_api_key(self) -> bool:
        """Check if required API key is available"""
        if not os.getenv('GEMINI_API_KEY'):
            print("❌ GEMINI_API_KEY not found in .env")
            return False
        print(f"✓ GEMINI_API_KEY found")
        return True

    def start_server(self) -> bool:
        """Start the Gemini voice agent server"""
        env = os.environ.copy()
        env['PROVIDER'] = 'gemini'
        env['PORT'] = '5002'

        cmd = [sys.executable, 'main.py']
        self.server_process = subprocess.Popen(
            cmd,
            cwd=self.project_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        # Wait for server to be ready
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
        """Run a single test scenario via text chat"""
        import socketio

        sio = socketio.Client()
        metrics = {'scenario': scenario, 'events': {}, 'errors': []}

        session_id = None
        events = {'session': threading.Event(), 'response': threading.Event()}

        @sio.on('session_started')
        def on_session(data):
            nonlocal session_id
            session_id = data.get('session_id')
            metrics['events']['session_started'] = time.time()
            events['session'].set()

        @sio.on('audio_chunk')
        def on_audio(data):
            if 'first_audio' not in metrics['events']:
                metrics['events']['first_audio'] = time.time()
                events['response'].set()

        @sio.on('error')
        def on_error(data):
            metrics['errors'].append(data.get('message', 'Unknown error'))
            events['response'].set()

        try:
            sio.connect('http://localhost:5002', wait_timeout=10)
            metrics['events']['start'] = time.time()

            sio.emit('start_session', {'table_id': '1'})
            if not events['session'].wait(timeout=5):
                raise Exception("Session timeout")

            messages = {
                'simple_order': "I'd like Kung Pao Chicken",
                'complex_order': "I want two orders of Dan Dan Noodles",
                'question': "What do you recommend?",
                'modification': "Actually, make that three instead",
                'greeting': "Hello, I'd like to place an order",
                'closing': "Thank you, that's all"
            }

            sio.emit('chat', {'session_id': session_id, 'message': messages.get(scenario, messages['simple_order'])})
            metrics['events']['chat_sent'] = time.time()

            if not events['response'].wait(timeout=30):
                metrics['errors'].append("Timeout")

            sio.disconnect()
            metrics['events']['end'] = time.time()

            if 'first_audio' in metrics['events']:
                metrics['total_response_ms'] = (
                    metrics['events']['first_audio'] - metrics['events']['chat_sent']
                ) * 1000

            return metrics

        except Exception as e:
            metrics['errors'].append(str(e))
            return metrics

    def run_all(self) -> Dict:
        """Run all tests"""
        print("\n" + "=" * 60)
        print("GEMINI STANDARD PROVIDER TESTS")
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
            'provider': 'gemini',
            'results': results,
            'passed': len(successes),
            'total': len(results)
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Test Gemini Standard Provider')
    parser.add_argument('-i', '--iterations', type=int, default=1, help='Iterations per scenario')
    args = parser.parse_args()

    tester = GeminiTester(iterations=args.iterations)
    results = tester.run_all()

    report_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"test_gemini_{int(time.time())}.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Report saved: {report_path}")

    return 0 if results.get('passed', 0) == results.get('total', 0) else 1


if __name__ == '__main__':
    sys.exit(main())
