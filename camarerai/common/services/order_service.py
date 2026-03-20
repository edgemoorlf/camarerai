"""
Order Service - Handles order processing logic
Processes function calls from LLM and manages order state
"""

import json
from camarerai import config


class OrderService:
    """Handles order processing logic"""

    @staticmethod
    def process_tool_call(tool_call_buffer, session):
        """
        Process update_order function call

        Args:
            tool_call_buffer: Dict with 'id', 'name', 'arguments'
            session: ConversationSession instance

        Returns:
            Dict with order update result or None if not an order update
        """
        if tool_call_buffer["name"] != "update_order":
            return None

        try:
            arguments = json.loads(tool_call_buffer["arguments"])
            action = arguments.get("action")
            items = arguments.get("items", [])

            print(f"[Order] Action: {action}, Items: {len(items)}")

            # Process order update based on session state
            if session.state == config.SessionState.CONFIRMED:
                OrderService._process_confirmed_state(action, items, session)
            elif session.state == config.SessionState.ORDERING:
                OrderService._process_ordering_state(action, items, session)

            # Calculate totals
            return OrderService.calculate_totals(session, action)

        except Exception as e:
            print(f"[Order] Error processing tool call: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _process_confirmed_state(action, items, session):
        """
        Process order in CONFIRMED state
        Only allow "add" action in confirmed state
        """
        if action in ['modify', 'remove']:
            print(f"[Order] Rejected {action} in CONFIRMED state")
        elif action == 'add':
            for item in items:
                session.current_order.append(item)
                print(f"[Order] Added (CONFIRMED state): {item['name']} x{item['quantity']} - ${item['price']}")

    @staticmethod
    def _process_ordering_state(action, items, session):
        """
        Process order in ORDERING state
        Allow all actions (add, modify, remove)
        """
        if action == 'add':
            for item in items:
                session.current_order.append(item)
                print(f"[Order] Added: {item['name']} x{item['quantity']} - ${item['price']}")

        elif action == 'remove':
            for item in items:
                item_name = item['name'].lower()
                session.current_order = [
                    o for o in session.current_order
                    if o['name'].lower() != item_name
                ]
                print(f"[Order] Removed: {item['name']}")

        elif action == 'modify':
            for item in items:
                item_name = item['name'].lower()
                found = False
                for o in session.current_order:
                    if o['name'].lower() == item_name:
                        o['quantity'] = item['quantity']
                        found = True
                        print(f"[Order] Modified: {item['name']} -> x{item['quantity']}")
                        break

                if not found:
                    session.current_order.append(item)
                    print(f"[Order] Added (via modify): {item['name']} x{item['quantity']}")

    @staticmethod
    def calculate_totals(session, action=None):
        """
        Calculate order totals

        Args:
            session: ConversationSession instance
            action: Optional action that triggered the calculation

        Returns:
            Dict with subtotal, tax, total, and item_count
        """
        all_items = session.confirmed_items + session.current_order
        subtotal = sum(item['price'] * item['quantity'] for item in all_items)
        tax = subtotal * config.TAX_RATE
        total = subtotal + tax

        result = {
            'subtotal': round(subtotal, 2),
            'tax': round(tax, 2),
            'total': round(total, 2),
            'item_count': len(all_items)
        }

        if action:
            result['action'] = action

        print(f"[Order] Total items: {len(all_items)}, Total: ${total:.2f}")

        return result
