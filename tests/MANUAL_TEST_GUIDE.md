"""
Manual Test Guide for Session Management

This guide provides step-by-step instructions for manually testing
the session management feature in a browser.
"""

# Session Management - Manual Test Guide

## Prerequisites

1. **Start the server:**
   ```bash
   python3 voice_agent.py
   ```

2. **Open browser:**
   ```
   http://localhost:5002
   ```

3. **Open browser console (F12)** to see debug messages

---

## Test Case 1: Basic Session Flow

### Steps:
1. Tap "Touch to Order" button
2. Complete enrollment: Say "Hello, I'd like to order"
3. Order items: "I'd like Kung Pao Chicken and Dan Dan Noodles"
4. Say "Thank you"

### Expected Results:
- ✓ Button changes to "Tap for Anything"
- ✓ Order remains visible on screen
- ✓ Items are grayed out (locked)
- ✓ Lock icon (🔒) appears next to "Confirmed Order"
- ✓ Console shows: `[Session] State transition: ORDERING → CONFIRMED`
- ✓ Console shows: `[Session] Locked 2 items`

### Console Output to Watch:
```
[Enrollment] ✓ Success - speaker enrolled
[Order] Added: Kung Pao Chicken x1 - $14.99
[Order] Added: Dan Dan Noodles x1 - $12.99
[Session] State transition: ORDERING → CONFIRMED
[Session] Locked 2 items
```

---

## Test Case 2: Adding More Items After Confirmation

### Steps:
1. Complete Test Case 1
2. Tap "Tap for Anything" button
3. Order more: "Add Spring Rolls"
4. Verify new item appears in "Additional Items" section
5. Say "Thank you" again

### Expected Results:
- ✓ "Tap for Anything" button hides when tapped
- ✓ New item appears in separate "Additional Items" section
- ✓ Confirmed items remain grayed out
- ✓ After second "Thank you", all items are locked
- ✓ Button reappears as "Tap for Anything"
- ✓ Console shows: `[Session] Additional confirmation in CONFIRMED state`

### Visual Check:
```
Your Order
├── Confirmed Order 🔒
│   ├── Kung Pao Chicken x1 - $14.99 (grayed out)
│   └── Dan Dan Noodles x1 - $12.99 (grayed out)
├── Additional Items
│   └── Spring Rolls x1 - $8.99 (normal)
└── Total: $56.64
```

After second "Thank you":
```
Your Order
├── Confirmed Order 🔒
│   ├── Kung Pao Chicken x1 - $14.99 (grayed out)
│   ├── Dan Dan Noodles x1 - $12.99 (grayed out)
│   └── Spring Rolls x1 - $8.99 (grayed out)
└── Total: $56.64
```

---

## Test Case 3: Modify Attempt (Should Fail)

### Steps:
1. Complete Test Case 1
2. Tap "Tap for Anything"
3. Try to modify: "Change the chicken to two"

### Expected Results:
- ✓ LLM refuses politely
- ✓ Response in appropriate language:
  - English: "Your order has been confirmed. I can add more items, but cannot modify the confirmed order. Would you like to add something else?"
  - Mandarin: "您的订单已确认。我可以添加更多菜品，但无法修改已确认的订单。您想添加其他菜品吗？"
  - Cantonese: "你嘅訂單已經確認咗。我可以加多啲嘢，但係唔可以改已經確認嘅訂單。你想加其他嘢嗎？"
- ✓ Order remains unchanged
- ✓ Console shows: `[Order] Rejected modify in CONFIRMED state` (if LLM tried to send modify action)

---

## Test Case 4: Remove Attempt (Should Fail)

### Steps:
1. Complete Test Case 1
2. Tap "Tap for Anything"
3. Try to remove: "Cancel the noodles"

### Expected Results:
- ✓ LLM refuses politely (same messages as Test Case 3)
- ✓ Order remains unchanged
- ✓ Console shows: `[Order] Rejected remove in CONFIRMED state` (if LLM tried to send remove action)

---

## Test Case 5: Manual Reset

### Steps:
1. Complete Test Case 1
2. Click "Reset Session (Staff)" button (bottom-left, red)
3. Confirm the dialog

### Expected Results:
- ✓ Confirmation dialog appears
- ✓ After confirming:
  - Order panel disappears
  - Status area disappears
  - "Touch to Order" button reappears
  - Console shows: `[Session] Manual reset for Table X`
  - Console shows: `[Session] Reset complete, ready for next customer`
- ✓ Ready for next customer

---

## Test Case 6: Multiple Confirmations

### Steps:
1. Order items: "Kung Pao Chicken"
2. Say "Thank you" → Items locked
3. Tap "Tap for Anything"
4. Order more: "Dan Dan Noodles"
5. Say "Thank you" → Items locked
6. Tap "Tap for Anything"
7. Order more: "Spring Rolls"
8. Say "Thank you" → Items locked

### Expected Results:
- ✓ After each "Thank you", items are locked
- ✓ All items accumulate in "Confirmed Order" section
- ✓ Totals update correctly
- ✓ Console shows confirmation messages for each round

### Final State:
```
Confirmed Order 🔒
├── Kung Pao Chicken x1 - $14.99
├── Dan Dan Noodles x1 - $12.99
└── Spring Rolls x1 - $8.99
Total: $56.64
```

---

## Test Case 7: Questions After Confirmation

### Steps:
1. Complete Test Case 1
2. Tap "Tap for Anything"
3. Ask: "How spicy is the Kung Pao Chicken?"

### Expected Results:
- ✓ LLM responds normally with information
- ✓ No ORDER_UPDATE generated
- ✓ Order remains unchanged
- ✓ Can continue conversation

---

## Test Case 8: Language Consistency

### Steps:
1. Test in English (Test Cases 1-7)
2. Reset session
3. Test in Mandarin:
   - "我要宫保鸡丁"
   - "谢谢"
4. Reset session
5. Test in Cantonese:
   - "我要宮保雞丁"
   - "唔該"

### Expected Results:
- ✓ LLM responds in same language as customer
- ✓ Closing remarks detected in all languages
- ✓ Refusal messages in appropriate language

---

## Test Case 9: Speaker Verification Integration

### Steps:
1. Complete enrollment with your voice
2. Order items and confirm
3. Tap "Tap for Anything"
4. Have another person speak

### Expected Results:
- ✓ Your voice triggers barge-in
- ✓ Other person's voice does NOT trigger barge-in
- ✓ Console shows:
  - `[Barge-in] ✓ Verified (similarity: 0.XXX)` for your voice
  - `[Barge-in] ✗ Rejected (similarity: 0.XXX)` for other voice

---

## Test Case 10: Edge Cases

### Test 10a: Empty Confirmation
**Steps:**
1. Tap "Touch to Order"
2. Complete enrollment
3. Say "Thank you" immediately (without ordering)

**Expected:**
- ✓ State transitions to CONFIRMED
- ✓ No items in confirmed list
- ✓ Button changes to "Tap for Anything"

### Test 10b: Rapid Confirmations
**Steps:**
1. Order item
2. Say "Thank you" quickly
3. Immediately tap "Tap for Anything"
4. Say "Thank you" again quickly

**Expected:**
- ✓ All state transitions work correctly
- ✓ No race conditions
- ✓ UI updates correctly

### Test 10c: Long Session
**Steps:**
1. Order items
2. Confirm
3. Add more items
4. Confirm
5. Repeat 5-10 times

**Expected:**
- ✓ All items accumulate correctly
- ✓ Totals calculate correctly
- ✓ No memory leaks
- ✓ UI remains responsive

---

## Debugging Tips

### Console Messages to Watch:

**Session State:**
```
[Session] State transition: ORDERING → CONFIRMED
[Session] Locked X items
[Session] Additional confirmation in CONFIRMED state
[Session] Manual reset for Table X
```

**Order Management:**
```
[Order] Added: Item Name xN - $XX.XX
[Order] Modified: Item Name -> xN
[Order] Removed: Item Name
[Order] Rejected modify in CONFIRMED state
[Order] Rejected remove in CONFIRMED state
```

**Speaker Verification:**
```
[Speaker] Enrolled: {f0: XXX, ...}
[Barge-in] ✓ Verified (similarity: 0.XXX)
[Barge-in] ✗ Rejected (similarity: 0.XXX)
```

### Common Issues:

**Issue: Button doesn't change to "Tap for Anything"**
- Check console for state_changed event
- Verify closing remark was detected
- Check if state is CONFIRMED

**Issue: Items not locked (not grayed out)**
- Check if confirmed_items array is populated
- Verify CSS classes are applied (.locked)
- Check browser console for errors

**Issue: Can still modify confirmed items**
- Check LLM prompt (should refuse in CONFIRMED state)
- Verify backend rejects modify/remove actions
- Check console for rejection messages

**Issue: Reset doesn't work**
- Check if reset button is visible
- Verify session_reset event is received
- Check if session_id is valid

---

## Success Criteria

All test cases should pass with:
- ✓ No console errors
- ✓ Correct state transitions
- ✓ Order locking works
- ✓ UI updates correctly
- ✓ LLM refuses modify/remove in CONFIRMED state
- ✓ Manual reset works
- ✓ Speaker verification still works

---

## Reporting Issues

If you find issues, report:
1. Test case number
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Console output
6. Screenshots (if UI issue)

---

**Last Updated:** 2026-02-05
**Branch:** feature/session-management
