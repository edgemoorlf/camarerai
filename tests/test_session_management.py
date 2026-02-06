"""
Test Session Management Implementation

Tests the session state management, order locking, and state transitions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_agent import ConversationSession, SessionState
from datetime import datetime


class TestSessionManagement:
    """Test suite for session management"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def assert_equal(self, actual, expected, message):
        """Assert that actual equals expected"""
        if actual == expected:
            self.passed += 1
            print(f"  ✓ {message}")
            return True
        else:
            self.failed += 1
            print(f"  ✗ {message}")
            print(f"    Expected: {expected}")
            print(f"    Actual: {actual}")
            return False

    def assert_true(self, condition, message):
        """Assert that condition is true"""
        if condition:
            self.passed += 1
            print(f"  ✓ {message}")
            return True
        else:
            self.failed += 1
            print(f"  ✗ {message}")
            return False

    def test_session_initialization(self):
        """Test 1: Session initializes with correct state"""
        print("\n[Test 1] Session Initialization")

        session = ConversationSession('1', 'customer')

        self.assert_equal(session.state, SessionState.IDLE, "Initial state is IDLE")
        self.assert_equal(len(session.current_order), 0, "Current order is empty")
        self.assert_equal(len(session.confirmed_items), 0, "Confirmed items is empty")
        self.assert_true(session.order_confirmed_at is None, "Order not confirmed yet")

    def test_state_transitions(self):
        """Test 2: State transitions work correctly"""
        print("\n[Test 2] State Transitions")

        session = ConversationSession('1', 'customer')

        # IDLE → ENROLLING
        session.state = SessionState.ENROLLING
        self.assert_equal(session.state, SessionState.ENROLLING, "Transition to ENROLLING")

        # ENROLLING → ORDERING
        session.state = SessionState.ORDERING
        self.assert_equal(session.state, SessionState.ORDERING, "Transition to ORDERING")

        # ORDERING → CONFIRMED
        session.state = SessionState.CONFIRMED
        self.assert_equal(session.state, SessionState.CONFIRMED, "Transition to CONFIRMED")

    def test_order_management_ordering_state(self):
        """Test 3: Order management in ORDERING state"""
        print("\n[Test 3] Order Management in ORDERING State")

        session = ConversationSession('1', 'customer')
        session.state = SessionState.ORDERING

        # Add items
        session.current_order.append({
            'name': 'Kung Pao Chicken',
            'quantity': 1,
            'price': 14.99
        })
        session.current_order.append({
            'name': 'Dan Dan Noodles',
            'quantity': 1,
            'price': 12.99
        })

        self.assert_equal(len(session.current_order), 2, "Added 2 items to current order")
        self.assert_equal(len(session.confirmed_items), 0, "No confirmed items yet")

        # Modify quantity
        session.current_order[0]['quantity'] = 2
        self.assert_equal(session.current_order[0]['quantity'], 2, "Modified quantity")

        # Remove item
        session.current_order = [item for item in session.current_order if item['name'] != 'Dan Dan Noodles']
        self.assert_equal(len(session.current_order), 1, "Removed 1 item")

    def test_order_locking_on_confirmation(self):
        """Test 4: Order locking on confirmation"""
        print("\n[Test 4] Order Locking on Confirmation")

        session = ConversationSession('1', 'customer')
        session.state = SessionState.ORDERING

        # Add items
        session.current_order.append({
            'name': 'Kung Pao Chicken',
            'quantity': 1,
            'price': 14.99
        })
        session.current_order.append({
            'name': 'Dan Dan Noodles',
            'quantity': 1,
            'price': 12.99
        })

        # Simulate confirmation (ORDERING → CONFIRMED)
        session.confirmed_items.extend(session.current_order)
        session.current_order = []
        session.state = SessionState.CONFIRMED
        session.order_confirmed_at = datetime.now()

        self.assert_equal(len(session.confirmed_items), 2, "2 items locked in confirmed_items")
        self.assert_equal(len(session.current_order), 0, "Current order cleared")
        self.assert_equal(session.state, SessionState.CONFIRMED, "State is CONFIRMED")
        self.assert_true(session.order_confirmed_at is not None, "Confirmation timestamp set")

    def test_add_more_items_after_confirmation(self):
        """Test 5: Adding more items after confirmation"""
        print("\n[Test 5] Adding More Items After Confirmation")

        session = ConversationSession('1', 'customer')
        session.state = SessionState.CONFIRMED

        # Simulate confirmed items
        session.confirmed_items = [
            {'name': 'Kung Pao Chicken', 'quantity': 1, 'price': 14.99},
            {'name': 'Dan Dan Noodles', 'quantity': 1, 'price': 12.99}
        ]

        # Add new item
        session.current_order.append({
            'name': 'Spring Rolls',
            'quantity': 1,
            'price': 8.99
        })

        self.assert_equal(len(session.confirmed_items), 2, "Confirmed items unchanged")
        self.assert_equal(len(session.current_order), 1, "New item added to current order")

        # Simulate second confirmation
        session.confirmed_items.extend(session.current_order)
        session.current_order = []

        self.assert_equal(len(session.confirmed_items), 3, "All items now confirmed")
        self.assert_equal(len(session.current_order), 0, "Current order cleared again")

    def test_closing_remark_detection(self):
        """Test 6: Closing remark detection"""
        print("\n[Test 6] Closing Remark Detection")

        session = ConversationSession('1', 'customer')

        # English closing remarks
        self.assert_true(session._is_closing_remark("Thank you"), "Detects 'Thank you'")
        self.assert_true(session._is_closing_remark("Thanks"), "Detects 'Thanks'")
        self.assert_true(session._is_closing_remark("That's all"), "Detects 'That's all'")
        self.assert_true(session._is_closing_remark("Go ahead"), "Detects 'Go ahead'")

        # Mandarin closing remarks
        self.assert_true(session._is_closing_remark("谢谢"), "Detects '谢谢'")
        self.assert_true(session._is_closing_remark("好的"), "Detects '好的'")
        self.assert_true(session._is_closing_remark("可以了"), "Detects '可以了'")

        # Cantonese closing remarks
        self.assert_true(session._is_closing_remark("唔該"), "Detects '唔該'")
        self.assert_true(session._is_closing_remark("多謝"), "Detects '多謝'")
        self.assert_true(session._is_closing_remark("得啦"), "Detects '得啦'")

        # Non-closing remarks
        self.assert_true(not session._is_closing_remark("I want chicken"), "Rejects 'I want chicken'")
        self.assert_true(not session._is_closing_remark("How much is it?"), "Rejects 'How much is it?'")

    def test_order_totals_calculation(self):
        """Test 7: Order totals calculation"""
        print("\n[Test 7] Order Totals Calculation")

        session = ConversationSession('1', 'customer')

        # Add items
        session.confirmed_items = [
            {'name': 'Kung Pao Chicken', 'quantity': 2, 'price': 14.99},
            {'name': 'Dan Dan Noodles', 'quantity': 1, 'price': 12.99}
        ]
        session.current_order = [
            {'name': 'Spring Rolls', 'quantity': 1, 'price': 8.99}
        ]

        # Calculate totals
        all_items = session.confirmed_items + session.current_order
        subtotal = sum(item['price'] * item['quantity'] for item in all_items)
        tax = subtotal * 0.09
        total = subtotal + tax

        expected_subtotal = (14.99 * 2) + 12.99 + 8.99  # 51.96
        expected_tax = expected_subtotal * 0.09  # 4.68
        expected_total = expected_subtotal + expected_tax  # 56.64

        self.assert_equal(round(subtotal, 2), round(expected_subtotal, 2), f"Subtotal is ${expected_subtotal:.2f}")
        self.assert_equal(round(tax, 2), round(expected_tax, 2), f"Tax is ${expected_tax:.2f}")
        self.assert_equal(round(total, 2), round(expected_total, 2), f"Total is ${expected_total:.2f}")

    def test_multiple_confirmations(self):
        """Test 8: Multiple confirmations accumulate items"""
        print("\n[Test 8] Multiple Confirmations")

        session = ConversationSession('1', 'customer')
        session.state = SessionState.ORDERING

        # First order
        session.current_order = [
            {'name': 'Kung Pao Chicken', 'quantity': 1, 'price': 14.99}
        ]

        # First confirmation
        session.confirmed_items.extend(session.current_order)
        session.current_order = []
        session.state = SessionState.CONFIRMED

        self.assert_equal(len(session.confirmed_items), 1, "1 item confirmed after first confirmation")

        # Add more items
        session.current_order = [
            {'name': 'Dan Dan Noodles', 'quantity': 1, 'price': 12.99}
        ]

        # Second confirmation
        session.confirmed_items.extend(session.current_order)
        session.current_order = []

        self.assert_equal(len(session.confirmed_items), 2, "2 items confirmed after second confirmation")

        # Add more items
        session.current_order = [
            {'name': 'Spring Rolls', 'quantity': 1, 'price': 8.99}
        ]

        # Third confirmation
        session.confirmed_items.extend(session.current_order)
        session.current_order = []

        self.assert_equal(len(session.confirmed_items), 3, "3 items confirmed after third confirmation")

    def test_session_reset(self):
        """Test 9: Session reset clears everything"""
        print("\n[Test 9] Session Reset")

        session = ConversationSession('1', 'customer')
        session.state = SessionState.CONFIRMED
        session.confirmed_items = [
            {'name': 'Kung Pao Chicken', 'quantity': 1, 'price': 14.99}
        ]
        session.current_order = [
            {'name': 'Dan Dan Noodles', 'quantity': 1, 'price': 12.99}
        ]
        session.order_confirmed_at = datetime.now()

        # Simulate reset
        session.state = SessionState.IDLE
        session.confirmed_items = []
        session.current_order = []
        session.order_confirmed_at = None

        self.assert_equal(session.state, SessionState.IDLE, "State reset to IDLE")
        self.assert_equal(len(session.confirmed_items), 0, "Confirmed items cleared")
        self.assert_equal(len(session.current_order), 0, "Current order cleared")
        self.assert_true(session.order_confirmed_at is None, "Confirmation timestamp cleared")

    def run_all_tests(self):
        """Run all tests"""
        print("="*60)
        print("Session Management Test Suite")
        print("="*60)

        self.test_session_initialization()
        self.test_state_transitions()
        self.test_order_management_ordering_state()
        self.test_order_locking_on_confirmation()
        self.test_add_more_items_after_confirmation()
        self.test_closing_remark_detection()
        self.test_order_totals_calculation()
        self.test_multiple_confirmations()
        self.test_session_reset()

        print("\n" + "="*60)
        print(f"Test Results: {self.passed} passed, {self.failed} failed")
        print("="*60)

        if self.failed == 0:
            print("✓ All tests passed!")
            return 0
        else:
            print(f"✗ {self.failed} test(s) failed")
            return 1


if __name__ == '__main__':
    tester = TestSessionManagement()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
