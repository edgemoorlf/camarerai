"""
Provider Comparison Tool

Automatically tests all providers and generates comparison report.

Usage:
    python tests/performance/compare_providers.py

This will:
1. Start each provider's server
2. Run performance tests
3. Generate comparison report

Environment:
    DASHSCOPE_API_KEY - Required for all providers
    GEMINI_API_KEY - Required for gemini and gemini_live
"""

import subprocess
import json
import time
import os
import sys
import signal
import glob
from typing import Dict, List, Optional
from datetime import datetime


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class ProviderComparator:
    """Compares performance across all providers"""

    def __init__(self, iterations: int = 5, timeout: int = 120):
        self.iterations = iterations
        self.timeout = timeout
        self.results: Dict[str, Optional[Dict]] = {}
        self.server_process = None

    def start_server(self, provider: str) -> bool:
        """Start the voice agent server with specified provider"""
        print(f"\n[Server] Starting {provider}...")

        env = os.environ.copy()
        env['PROVIDER'] = provider

        try:
            self.server_process = subprocess.Popen(
                ['python3', 'main.py'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )

            # Wait for server to start
            import urllib.request
            for i in range(30):  # 30 seconds max
                time.sleep(1)
                try:
                    urllib.request.urlopen('http://localhost:5002', timeout=2)
                    print(f"[Server] {provider} ready")
                    return True
                except:
                    # Check if process crashed
                    if self.server_process.poll() is not None:
                        stdout, stderr = self.server_process.communicate()
                        print(f"[Server] Failed to start:")
                        print(stderr.decode() if stderr else stdout.decode())
                        return False

            print(f"[Server] Timeout waiting for {provider}")
            return False

        except Exception as e:
            print(f"[Server] Error starting {provider}: {e}")
            return False

    def stop_server(self):
        """Stop the running server"""
        if self.server_process:
            try:
                self.server_process.send_signal(signal.SIGTERM)
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            except:
                pass
            finally:
                self.server_process = None

    def run_tests(self, provider: str) -> Optional[Dict]:
        """Run performance tests for a provider"""
        print(f"\n[Tests] Running {self.iterations} iterations...")

        try:
            result = subprocess.run(
                [
                    'python3',
                    'tests/performance/run_performance_tests.py',
                    provider,
                    '--iterations', str(self.iterations)
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            print(result.stdout)

            if result.returncode != 0:
                print(f"[Tests] Error: {result.stderr}")
                return None

            # Find latest report
            reports_dir = 'tests/reports'
            pattern = f'{reports_dir}/perf_report_{provider}_*.json'
            reports = glob.glob(pattern)

            if reports:
                latest = max(reports, key=os.path.getctime)
                with open(latest) as f:
                    return json.load(f)

            return None

        except subprocess.TimeoutExpired:
            print(f"[Tests] Timeout after {self.timeout}s")
            return None
        except Exception as e:
            print(f"[Tests] Error: {e}")
            return None

    def compare_all(self) -> Dict:
        """Test all providers and generate comparison"""
        providers = ['dashscope', 'gemini', 'gemini_live']

        for provider in providers:
            print(f"\n{'='*70}")
            print(f"TESTING PROVIDER: {provider.upper()}")
            print(f"{'='*70}")

            # Start server
            if not self.start_server(provider):
                self.results[provider] = None
                continue

            # Wait a bit for initialization
            time.sleep(2)

            # Run tests
            result = self.run_tests(provider)
            self.results[provider] = result

            # Stop server
            self.stop_server()
            time.sleep(2)  # Cleanup time

        return self.generate_comparison_report()

    def generate_comparison_report(self) -> Dict:
        """Generate comparison report from all results"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'iterations': self.iterations,
            'providers': {},
            'comparison': {}
        }

        # Extract summary from each provider
        for provider, result in self.results.items():
            if result:
                report['providers'][provider] = result.get('summary', {})

        # Generate comparison table for each metric
        metrics = [
            'llm_first_token_ms',
            'tts_first_audio_ms',
            'total_response_ms',
            'transcription_latency_ms'
        ]

        for metric in metrics:
            comparison = {}
            for provider, summary in report['providers'].items():
                if metric in summary:
                    comparison[provider] = summary[metric]

            if comparison:
                report['comparison'][metric] = comparison

        return report

    def save_comparison(self, report: Dict) -> str:
        """Save comparison report to file"""
        reports_dir = 'tests/reports'
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = int(time.time())
        filename = f'comparison_{timestamp}.json'
        filepath = os.path.join(reports_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        return filepath

    def print_comparison(self, report: Dict):
        """Print comparison table to console"""
        print()
        print("=" * 70)
        print("PROVIDER COMPARISON REPORT")
        print("=" * 70)
        print()

        # Print each metric comparison
        for metric, providers in report['comparison'].items():
            metric_name = metric.replace('_ms', '').replace('_', ' ').title()
            print(f"\n{metric_name}")
            print("-" * 70)

            # Header
            print(f"{'Provider':<15} {'Avg':<10} {'Min':<10} {'Max':<10} {'P95':<10} {'Status':<10}")
            print("-" * 70)

            # Sort by average
            sorted_providers = sorted(
                providers.items(),
                key=lambda x: x[1].get('avg', float('inf'))
            )

            # Find best (lowest) average for highlighting
            best_avg = sorted_providers[0][1].get('avg', float('inf')) if sorted_providers else 0

            for provider, stats in sorted_providers:
                avg = stats.get('avg', 0)
                marker = "★" if avg == best_avg else " "

                print(f"{marker}{provider:<14} "
                      f"{avg:<10.0f} "
                      f"{stats.get('min', 0):<10.0f} "
                      f"{stats.get('max', 0):<10.0f} "
                      f"{stats.get('p95', 0):<10.0f} "
                      f"{'✅' if stats else '❌'}")

        # Overall recommendation
        print()
        print("OVERALL RECOMMENDATION")
        print("-" * 70)

        # Find best provider for each metric
        best_providers = {}
        for metric, providers in report['comparison'].items():
            if providers:
                best = min(providers.items(), key=lambda x: x[1].get('avg', float('inf')))
                best_providers[metric] = best[0]

        if best_providers:
            # Count wins per provider
            wins = {}
            for metric, provider in best_providers.items():
                wins[provider] = wins.get(provider, 0) + 1

            # Find overall winner
            winner = max(wins.items(), key=lambda x: x[1])
            print(f"🏆 Best Overall: {winner[0]} ({winner[1]}/{len(best_providers)} metrics)")
            print()

            for metric, provider in best_providers.items():
                metric_name = metric.replace('_ms', '').replace('_', ' ').title()
                print(f"  • {metric_name}: {provider}")

        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Compare all providers')
    parser.add_argument('--iterations', '-i', type=int, default=5,
                        help='Iterations per scenario')
    parser.add_argument('--timeout', '-t', type=int, default=120,
                        help='Timeout per provider in seconds')
    parser.add_argument('--providers', '-p', nargs='+',
                        choices=['dashscope', 'gemini', 'gemini_live'],
                        help='Specific providers to test')

    args = parser.parse_args()

    # Check API keys
    if not os.getenv('DASHSCOPE_API_KEY'):
        print("Error: DASHSCOPE_API_KEY not set")
        sys.exit(1)

    comparator = ProviderComparator(
        iterations=args.iterations,
        timeout=args.timeout
    )

    try:
        if args.providers:
            # Test specific providers only
            for provider in args.providers:
                print(f"\n{'='*70}")
                print(f"TESTING PROVIDER: {provider.upper()}")
                print(f"{'='*70}")

                if comparator.start_server(provider):
                    time.sleep(2)
                    result = comparator.run_tests(provider)
                    comparator.results[provider] = result
                    comparator.stop_server()
                    time.sleep(2)

            report = comparator.generate_comparison_report()
        else:
            # Test all providers
            report = comparator.compare_all()

        # Save and print
        filepath = comparator.save_comparison(report)
        comparator.print_comparison(report)

        print(f"Full report saved to: {filepath}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        comparator.stop_server()


if __name__ == '__main__':
    main()
