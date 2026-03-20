#!/usr/bin/env python3
"""
Gemini Live Performance Tests
"""

import subprocess
import json
import time
import os
import sys
import threading
import base64
from datetime import datetime
from typing import Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv()


class GeminiLivePerformanceTester:
    def __init__(self, iterations: int = 3):
        self.iterations = iterations
        self.project_root = os.path.join(os.path.dirname(__file__), '..')
        self.server_process = None
        self.results = []
        self.audio_dir = os.path.join(self.project_root, 'tests', 'fixtures')

    def start_server(self) -> bool:
        env = os.environ.copy()
        env['PROVIDER'] = 'gemini_live'
        env['PORT'] = '5002'

        cmd = [sys.executable, 'main.py']
        self.server_process = subprocess.Popen(cmd, cwd=self.project_root, env=env,
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for _ in range(30):
            try:
                import urllib.request
                urllib.request.urlopen('http://localhost:5002', timeout=1)
                return True
            except:
                time.sleep(0.5)
        return False

    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()

    def run_scenario(self, scenario: str) -> Optional[Dict]:
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
                metrics['total_response_ms'] = int(
                    (metrics['events']['first_audio'] - metrics['events']['audio_stream_start']) * 1000
                )
            return metrics
        except Exception as e:
            metrics['errors'].append(str(e))
            return metrics

    def run_all(self) -> Dict:
        print("\n" + "=" * 60)
        print("GEMINI LIVE PERFORMANCE TESTS")
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

        successes = [r for r in self.results if 'total_response_ms' in r]
        summary = {}
        if successes:
            times = [r['total_response_ms'] for r in successes]
            summary = {'avg_ms': sum(times) / len(times), 'min_ms': min(times), 'max_ms': max(times)}
            print(f"\n✓ {len(successes)}/{len(self.results)} tests passed, Avg: {summary['avg_ms']:.0f}ms")

        return {'provider': 'gemini_live', 'timestamp': datetime.now().isoformat(),
                'iterations': self.iterations, 'summary': summary,
                'results': self.results, 'passed': len(successes), 'total': len(self.results)}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Gemini Live Performance Tests')
    parser.add_argument('-i', '--iterations', type=int, default=3)
    args = parser.parse_args()

    tester = GeminiLivePerformanceTester(iterations=args.iterations)
    results = tester.run_all()

    report_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"perf_gemini_live_{int(time.time())}.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Report: {report_path}")
    return 0 if results.get('passed', 0) == results.get('total', 0) else 1


if __name__ == '__main__':
    sys.exit(main())
