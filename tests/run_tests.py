"""
Test Runner Script

Runs all tests for session management feature.
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("Session Management Test Suite")
    print("="*60)
    print("\nRunning automated tests...")

    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    results = []

    # Test 1: Unit tests
    success = run_command(
        "python3 tests/test_session_management.py",
        "Test 1: Unit Tests (Session State Management)"
    )
    results.append(("Unit Tests", success))

    # Test 2: Integration tests (requires manual server start)
    print("\n" + "="*60)
    print("Test 2: Integration Tests (WebSocket Communication)")
    print("="*60)
    print("\nNote: Integration tests require the server to be running.")
    print("To run integration tests:")
    print("  1. Start server: python3 voice_agent.py")
    print("  2. In another terminal: python3 tests/test_integration.py")
    print("\nSkipping integration tests for now...")
    results.append(("Integration Tests", None))

    # Test 3: Manual tests
    print("\n" + "="*60)
    print("Test 3: Manual Tests (Browser Testing)")
    print("="*60)
    print("\nManual tests require browser interaction.")
    print("See: tests/MANUAL_TEST_GUIDE.md")
    print("\nTo run manual tests:")
    print("  1. Start server: python3 voice_agent.py")
    print("  2. Open browser: http://localhost:5002")
    print("  3. Follow test guide: tests/MANUAL_TEST_GUIDE.md")
    results.append(("Manual Tests", None))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for test_name, success in results:
        if success is True:
            print(f"  ✓ {test_name}: PASSED")
        elif success is False:
            print(f"  ✗ {test_name}: FAILED")
        else:
            print(f"  ⊘ {test_name}: SKIPPED (requires manual execution)")

    # Exit code
    failed = sum(1 for _, success in results if success is False)

    print("\n" + "="*60)
    if failed == 0:
        print("✓ All automated tests passed!")
        print("\nNext steps:")
        print("  1. Run integration tests (see above)")
        print("  2. Run manual tests in browser (see tests/MANUAL_TEST_GUIDE.md)")
        return 0
    else:
        print(f"✗ {failed} test suite(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
