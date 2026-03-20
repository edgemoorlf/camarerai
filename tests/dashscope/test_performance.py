#!/usr/bin/env python3
"""
DashScope Performance Tests
Measures actual latency metrics for DashScope provider
"""

import subprocess
import json
import time
import os
import sys
import threading
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()


class DashScopePerformanceTester:
    """Performance test runner for DashScope provider"""

    def __init__(self, iterations: int = 5):
        self.iterations = iterations
        self.project_root = os.path.join(os.path.dirname(__file__), '..')
        self.server_process = None
        self.results = []

    def start_server(self) -> bool:
        """Start the DashScope voice agent server"""
        env = os.environ.copy()
        env['PROVIDER'] = 'dashscope'
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

    def run_scenario(self, scenario: str) -> Optional[Dict]:
        """Run a single test scenario"""
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
                metrics['total_response_ms'] = int(
                    (metrics['events']['first_audio'] - metrics['events']['chat_sent']) * 1000
                )

            return metrics

        except Exception as e:
            metrics['errors'].append(str(e))
            return metrics

    def run_all(self) -> Dict:
        """Run all performance tests"""
        print("\n" + "=" * 60)
        print("DASHSCOPE PERFORMANCE TESTS")
        print("=" * 60)

        if not self.start_server():
            return {'error': 'Server failed to start'}

        time.sleep(2)

        scenarios = ['simple_order', 'complex_order', 'question', 'modification', 'greeting', 'closing']

        for scenario in scenarios:
            for i in range(self.iterations):
                print(f"  {scenario} ({i+1}/{self.iterations})...", end=' ', flush=True)
                result = self.run_scenario(scenario)
                if result.get('total_response_ms'):
                    print(f"✓ {result['total_response_ms']}ms")
                else:
                    print(f"❌ {result.get('errors', ['Unknown'])[0]}")
                self.results.append(result)

        self.stop_server()

        # Calculate summary
        successes = [r for r in self.results if 'total_response_ms' in r]
        summary = {}
        if successes:
            times = [r['total_response_ms'] for r in successes]
            summary = {
                'avg_ms': sum(times) / len(times),
                'min_ms': min(times),
                'max_ms': max(times),
                'p95_ms': sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0]
            }
            print(f"\n✓ {len(successes)}/{len(self.results)} tests passed")
            print(f"  Average: {summary['avg_ms']:.0f}ms")
            print(f"  Min/Max: {summary['min_ms']:.0f}ms / {summary['max_ms']:.0f}ms")

        return {
            'provider': 'dashscope',
            'timestamp': datetime.now().isoformat(),
            'iterations': self.iterations,
            'summary': summary,
            'results': self.results,
            'passed': len(successes),
            'total': len(self.results)
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='DashScope Performance Tests')
    parser.add_argument('-i', '--iterations', type=int, default=3, help='Iterations per scenario')
    args = parser.parse_args()

    tester = DashScopePerformanceTester(iterations=args.iterations)
    results = tester.run_all()

    # Save report
    report_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"perf_dashscope_{int(time.time())}.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Report: {report_path}")

    return 0 if results.get('passed', 0) == results.get('total', 0) else 1


if __name__ == '__main__':
    sys.exit(main())
