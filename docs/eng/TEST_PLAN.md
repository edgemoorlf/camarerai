# Test Plan: Voice Ordering System v0.5

**Last Updated:** 2026-02-04
**Version:** v0.5 (Order Management)
**Test Environment:** Local development (http://localhost:5002)

---

## Test Objectives

1. Verify Touch to Order button works and complies with browser security
2. Verify always-listening mode activates after button tap
3. Verify natural conversation flow with auto-respond
4. Verify order parsing from natural language (English, Mandarin, Cantonese)
5. Verify order display updates in real-time
6. Verify order calculations are accurate
7. Verify order modifications (add/remove/modify) work correctly
8. Verify closing remark detection triggers session reset
9. Verify session boundaries are clean between customers
10. Verify barge-in functionality works

---

## Pre-Test Setup

### 1. Environment Check
```bash
# Verify server is not running
lsof -ti:5002 | xargs kill -9 2>/dev/null

# Start server
python3 voice_agent.py
```

**Expected Output:**
```
[Server] Starting on http://127.0.0.1:5002
[Server] Network: http://192.168.1.139:5002
```

### 2. Browser Setup
- Open Chrome/Firefox/Safari
- Navigate to: `http://localhost:5002`
- Open DevTools (F12) → Console tab
- Keep console visible for debugging

### 3. Audio Setup
- Ensure microphone is connected and working
- Test microphone in system settings
- Ensure speakers/headphones are connected
- Set volume to comfortable level

---

## Test Scenarios

### Test Suite 1: Initial Load & Button

#### Test 1.1: Page Load
**Objective:** Verify page loads correctly with Touch to Order button

**Steps:**
1. Open `http://localhost:5002`
2. Observe page load

**Expected Results:**
- ✅ Page loads without errors
- ✅ "Touch to Order" button is visible and prominent
- ✅ Button shows microphone icon (🎤)
- ✅ Button text: "Touch to Order"
- ✅ Button subtitle: "Tap to start voice ordering"
- ✅ Status area is hidden
- ✅ Order panel shows "No items yet"
- ✅ Totals show $0.00
- ✅ "Send to Kitchen" button is disabled
- ✅ Debug button (🐛) visible in bottom right

**Console Check:**
- Should see: "Ready. Waiting for user to tap 'Touch to Order' button..."

**Pass Criteria:** All expected results present, no console errors

---

#### Test 1.2: Button Interaction
**Objective:** Verify button responds to hover and click

**Steps:**
1. Hover over "Touch to Order" button
2. Observe hover effect
3. Click button

**Expected Results:**
- ✅ Button lifts on hover (translateY effect)
- ✅ Shadow increases on hover
- ✅ Button responds to click
- ✅ Browser requests microphone permission

**Pass Criteria:** Button interactive, permission dialog appears

---

#### Test 1.3: Microphone Permission
**Objective:** Verify microphone permission flow

**Steps:**
1. Click "Touch to Order" button
2. Browser shows permission dialog
3. Click "Allow"

**Expected Results:**
- ✅ Permission dialog appears
- ✅ After allowing, button disappears
- ✅ Status indicator appears showing "Listening"
- ✅ Status icon shows ◉
- ✅ Console shows: "User tapped 'Touch to Order' - starting microphone..."
- ✅ Console shows: "✓ Always-listening mode active"

**Console Check:**
- "WebSocket connected"
- "Session created: [session_id]"
- "Recognition started"

**Pass Criteria:** Microphone activates, status shows "Listening"

---

### Test Suite 2: Basic Ordering (English)

#### Test 2.1: Single Item Order
**Objective:** Verify basic order parsing and display

**Test Data:**
- Say: "I'd like the Kung Pao Chicken"

**Expected Results:**
- ✅ Status changes: Listening → Thinking → Speaking → Listening
- ✅ AI responds: "Great choice! One Kung Pao Chicken coming up." (or similar)
- ✅ Order panel updates with:
  - Item name: "Kung Pao Chicken"
  - Quantity: x1 (or no badge if quantity is 1)
  - Price: $14.99
  - Subtotal: $14.99
  - Tax: $1.35
  - Total: $16.34
- ✅ Item count shows "1 item"
- ✅ "Send to Kitchen" button enabled

**Console Check:**
- "Transcription complete: I'd like the Kung Pao Chicken"
- "Chat response: [AI response]"
- "Order updated: [order data]"
- "[Order] Added: Kung Pao Chicken x1 - $14.99"

**Pass Criteria:** Item appears in order panel with correct price and calculations

---

#### Test 2.2: Multiple Items at Once
**Objective:** Verify parsing multiple items in one utterance

**Test Data:**
- Say: "I'd like the Kung Pao Chicken and the Dan Dan Noodles"

**Expected Results:**
- ✅ AI acknowledges both items
- ✅ Order panel shows:
  - Kung Pao Chicken x1 - $14.99
  - Dan Dan Noodles x1 - $13.99
  - Subtotal: $28.98
  - Tax: $2.61
  - Total: $31.59
- ✅ Item count shows "2 items"

**Pass Criteria:** Both items appear, calculations correct

---

#### Test 2.3: Sequential Ordering
**Objective:** Verify adding items one at a time

**Test Data:**
1. Say: "I'd like the Kung Pao Chicken"
2. Wait for AI response
3. Say: "And the Dan Dan Noodles"
4. Wait for AI response
5. Say: "Also the Spring Rolls"

**Expected Results:**
- ✅ Each item added sequentially
- ✅ Order panel updates after each addition
- ✅ Final order shows:
  - Kung Pao Chicken x1 - $14.99
  - Dan Dan Noodles x1 - $13.99
  - Spring Rolls x1 - $8.99
  - Subtotal: $37.97
  - Tax: $3.42
  - Total: $41.39
- ✅ Item count shows "3 items"

**Pass Criteria:** All items added, totals correct

---

### Test Suite 3: Order Modifications

#### Test 3.1: Increase Quantity
**Objective:** Verify quantity modification

**Setup:**
- Order "Kung Pao Chicken" first

**Test Data:**
- Say: "Actually, make that two"

**Expected Results:**
- ✅ AI responds: "No problem! I'll change that to two orders." (or similar)
- ✅ Order panel updates:
  - Kung Pao Chicken x2 - $29.98
  - Subtotal: $29.98
  - Tax: $2.70
  - Total: $32.68
- ✅ Quantity badge shows "x2"

**Console Check:**
- "[Order] Modified: Kung Pao Chicken -> x2"

**Pass Criteria:** Quantity updates, price doubles, totals recalculate

---

#### Test 3.2: Change to Specific Quantity
**Objective:** Verify explicit quantity change

**Setup:**
- Order "Kung Pao Chicken x2"

**Test Data:**
- Say: "Change that to three"

**Expected Results:**
- ✅ Order panel updates:
  - Kung Pao Chicken x3 - $44.97
  - Subtotal: $44.97
  - Tax: $4.05
  - Total: $49.02
- ✅ Quantity badge shows "x3"

**Pass Criteria:** Quantity updates to 3, calculations correct

---

#### Test 3.3: Remove Item
**Objective:** Verify item removal

**Setup:**
- Order "Kung Pao Chicken" and "Dan Dan Noodles"

**Test Data:**
- Say: "Cancel the noodles" OR "Remove the Dan Dan Noodles"

**Expected Results:**
- ✅ AI responds: "Sure, I'll remove the Dan Dan Noodles from your order." (or similar)
- ✅ Dan Dan Noodles disappears from order panel
- ✅ Only Kung Pao Chicken remains
- ✅ Totals recalculate for remaining items
- ✅ Item count decreases

**Console Check:**
- "[Order] Removed: Dan Dan Noodles"

**Pass Criteria:** Item removed, totals recalculate correctly

---

### Test Suite 4: Multilingual Ordering

#### Test 4.1: Mandarin Ordering
**Objective:** Verify Mandarin language support

**Test Data:**
- Say: "我要宫保鸡丁"

**Expected Results:**
- ✅ AI responds in Mandarin
- ✅ Order panel shows: "宫保鸡丁" (or "Kung Pao Chicken")
- ✅ Price: $14.99
- ✅ Calculations correct

**Pass Criteria:** AI responds in Mandarin, order parsed correctly

---

#### Test 4.2: Cantonese Ordering
**Objective:** Verify Cantonese language support

**Test Data:**
- Say: "我要宮保雞丁"

**Expected Results:**
- ✅ AI responds in Cantonese
- ✅ Order panel shows item
- ✅ Price and calculations correct

**Pass Criteria:** AI responds in Cantonese, order parsed correctly

---

#### Test 4.3: Language Switching
**Objective:** Verify switching between languages

**Test Data:**
1. Say: "I'd like the Kung Pao Chicken" (English)
2. Say: "还要担担面" (Mandarin)
3. Say: "Thank you" (English)

**Expected Results:**
- ✅ AI responds in appropriate language for each utterance
- ✅ Both items added to order
- ✅ Session resets on "Thank you"

**Pass Criteria:** Language switching works, order parsing unaffected

---

### Test Suite 5: Closing Remarks & Session Reset

#### Test 5.1: English Closing Remarks
**Objective:** Verify English closing detection

**Setup:**
- Have items in order

**Test Data (try each separately):**
- "Thank you"
- "Thanks"
- "That's all"
- "Go ahead"
- "Send the order"

**Expected Results:**
- ✅ AI responds with confirmation
- ✅ After AI finishes speaking:
  - Microphone stops
  - Status indicator disappears
  - Order panel clears (shows "No items yet")
  - Totals reset to $0.00
  - "Send to Kitchen" button disabled
  - "Touch to Order" button reappears

**Console Check:**
- "Closing remark detected - will reset after AI response"
- "Closing remark detected - resetting to 'Touch to Order'"
- "Recording stopped"
- "Ready for next customer. Tap 'Touch to Order' to start."

**Pass Criteria:** Session resets completely, ready for next customer

---

#### Test 5.2: Mandarin Closing Remarks
**Objective:** Verify Mandarin closing detection

**Test Data (try each):**
- "谢谢"
- "好的"
- "可以了"
- "就这些"

**Expected Results:**
- ✅ Same as Test 5.1
- ✅ AI responds in Mandarin

**Pass Criteria:** Session resets on Mandarin closing remarks

---

#### Test 5.3: Cantonese Closing Remarks
**Objective:** Verify Cantonese closing detection

**Test Data (try each):**
- "唔該"
- "多謝"
- "得啦"
- "可以啦"

**Expected Results:**
- ✅ Same as Test 5.1
- ✅ AI responds in Cantonese

**Pass Criteria:** Session resets on Cantonese closing remarks

---

### Test Suite 6: Barge-in Functionality

#### Test 6.1: Voice Barge-in
**Objective:** Verify interrupting AI by speaking

**Steps:**
1. Order an item
2. While AI is speaking, start talking
3. Say something like "Wait" or "Actually"

**Expected Results:**
- ✅ AI stops speaking immediately
- ✅ Status returns to "Listening"
- ✅ Your new speech is processed

**Console Check:**
- "Barge-in detected - stopping speech"

**Pass Criteria:** AI stops immediately when interrupted

---

#### Test 6.2: Keyboard Barge-in
**Objective:** Verify interrupting AI with SPACE key

**Steps:**
1. Order an item
2. While AI is speaking, press SPACE key

**Expected Results:**
- ✅ AI stops speaking immediately
- ✅ Status returns to "Listening"

**Pass Criteria:** SPACE key interrupts AI speech

---

### Test Suite 7: Calculations Accuracy

#### Test 7.1: Single Item Calculation
**Test Data:**
- Kung Pao Chicken x1 @ $14.99

**Expected:**
- Subtotal: $14.99
- Tax (9%): $1.35
- Total: $16.34

**Pass Criteria:** All values match exactly

---

#### Test 7.2: Multiple Items Calculation
**Test Data:**
- Kung Pao Chicken x2 @ $14.99 = $29.98
- Dan Dan Noodles x1 @ $13.99 = $13.99

**Expected:**
- Subtotal: $43.97
- Tax (9%): $3.96
- Total: $47.93

**Pass Criteria:** All values match exactly

---

#### Test 7.3: Complex Order Calculation
**Test Data:**
- Kung Pao Chicken x3 @ $14.99 = $44.97
- Dan Dan Noodles x2 @ $13.99 = $27.98
- Spring Rolls x1 @ $8.99 = $8.99

**Expected:**
- Subtotal: $81.94
- Tax (9%): $7.37
- Total: $89.31

**Pass Criteria:** All values match exactly

---

### Test Suite 8: Edge Cases

#### Test 8.1: Empty Order Closing
**Objective:** Verify closing without ordering

**Steps:**
1. Tap "Touch to Order"
2. Immediately say "Thank you"

**Expected Results:**
- ✅ AI responds
- ✅ Session resets
- ✅ No errors

**Pass Criteria:** Handles gracefully

---

#### Test 8.2: Invalid Item Name
**Objective:** Verify handling of non-menu items

**Test Data:**
- Say: "I'd like a hamburger"

**Expected Results:**
- ✅ AI responds politely (e.g., "I'm sorry, we don't have hamburgers")
- ✅ No item added to order
- ✅ No errors

**Pass Criteria:** Handles gracefully, no crashes

---

#### Test 8.3: Unclear Speech
**Objective:** Verify handling of unclear transcription

**Test Data:**
- Mumble or speak very quietly

**Expected Results:**
- ✅ AI may ask for clarification
- ✅ No crashes
- ✅ Can continue conversation

**Pass Criteria:** System remains stable

---

#### Test 8.4: Very Long Order
**Objective:** Verify handling of many items

**Test Data:**
- Order 10+ different items

**Expected Results:**
- ✅ All items added
- ✅ Order panel scrolls if needed
- ✅ Calculations remain accurate
- ✅ No performance issues

**Pass Criteria:** System handles large orders

---

#### Test 8.5: Rapid Modifications
**Objective:** Verify handling of quick changes

**Test Data:**
1. "Kung Pao Chicken"
2. "Make that two"
3. "Actually three"
4. "No, just one"

**Expected Results:**
- ✅ Each modification processed
- ✅ Final quantity correct
- ✅ No race conditions

**Pass Criteria:** Final state is correct

---

### Test Suite 9: Multiple Sessions

#### Test 9.1: Sequential Customers
**Objective:** Verify clean session boundaries

**Steps:**
1. Complete full order → say "Thank you" → session resets
2. Tap "Touch to Order" again
3. Complete another order → say "Thank you"
4. Repeat 3 times

**Expected Results:**
- ✅ Each session independent
- ✅ Orders don't mix between sessions
- ✅ Button reappears each time
- ✅ No memory leaks or slowdowns

**Pass Criteria:** All sessions clean and independent

---

### Test Suite 10: Debug Panel

#### Test 10.1: Debug Panel Toggle
**Objective:** Verify debug panel functionality

**Steps:**
1. Click 🐛 button (bottom right)
2. Observe debug panel
3. Click × to close

**Expected Results:**
- ✅ Panel opens showing:
  - Session ID
  - Table name
  - Transcript
  - Response
- ✅ Panel closes on ×
- ✅ Button reappears

**Pass Criteria:** Debug panel works correctly

---

## Test Execution Checklist

### Pre-Test
- [ ] Server running without errors
- [ ] Browser console open
- [ ] Microphone working
- [ ] Speakers working
- [ ] Network stable

### Core Functionality
- [ ] Test Suite 1: Initial Load & Button (3 tests)
- [ ] Test Suite 2: Basic Ordering (3 tests)
- [ ] Test Suite 3: Order Modifications (3 tests)
- [ ] Test Suite 4: Multilingual Ordering (3 tests)
- [ ] Test Suite 5: Closing Remarks (3 tests)
- [ ] Test Suite 6: Barge-in (2 tests)
- [ ] Test Suite 7: Calculations (3 tests)

### Edge Cases
- [ ] Test Suite 8: Edge Cases (5 tests)
- [ ] Test Suite 9: Multiple Sessions (1 test)
- [ ] Test Suite 10: Debug Panel (1 test)

### Total Tests: 27

---

## Known Limitations (Expected Behavior)

### 1. Item Matching
- **Limitation:** Must say exact menu item name
- **Example:** "chicken" won't match "Kung Pao Chicken"
- **Expected:** AI may ask for clarification or not add item
- **Not a Bug:** This is expected behavior

### 2. LLM Variability
- **Limitation:** LLM responses may vary
- **Example:** Sometimes extracts ORDER_UPDATE, sometimes doesn't
- **Expected:** ~80-90% accuracy
- **Not a Bug:** This is expected LLM behavior

### 3. Modifications
- **Limitation:** Modifications not validated
- **Example:** Can say "no peanuts" for any item
- **Expected:** Modification stored but not validated
- **Not a Bug:** Validation not implemented yet

### 4. Context
- **Limitation:** Long conversations may lose context
- **Example:** After 10+ exchanges, may forget earlier items
- **Expected:** Keep conversations focused
- **Not a Bug:** Full context management not implemented yet

---

## Bug Reporting Template

If you find a bug, report it with:

```
**Bug Title:** [Short description]

**Test:** [Test number, e.g., Test 2.1]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happened]

**Console Output:**
[Paste relevant console output]

**Server Output:**
[Paste relevant server output]

**Severity:**
- [ ] Critical (blocks testing)
- [ ] High (major feature broken)
- [ ] Medium (feature partially works)
- [ ] Low (minor issue)
```

---

## Success Criteria

### Minimum Viable (Must Pass)
- ✅ Touch to Order button works
- ✅ Microphone activates
- ✅ Can order at least one item
- ✅ Order appears in panel
- ✅ Calculations are correct
- ✅ Session resets on closing remark

### Full Success (Should Pass)
- ✅ All core functionality tests pass (Suites 1-7)
- ✅ At least 80% of edge case tests pass (Suite 8)
- ✅ Multiple sessions work (Suite 9)
- ✅ Multilingual support works (Suite 4)

### Excellent (Nice to Have)
- ✅ All 27 tests pass
- ✅ No console errors
- ✅ Smooth user experience
- ✅ Fast response times (< 2s)

---

## Test Report Template

After testing, fill out:

```
# Test Report: Voice Ordering System v0.5

**Date:** [Date]
**Tester:** [Name]
**Environment:** [Browser, OS]

## Summary
- Total Tests: 27
- Passed: [X]
- Failed: [Y]
- Skipped: [Z]

## Core Functionality
- Suite 1 (Initial Load): [X/3] passed
- Suite 2 (Basic Ordering): [X/3] passed
- Suite 3 (Modifications): [X/3] passed
- Suite 4 (Multilingual): [X/3] passed
- Suite 5 (Closing Remarks): [X/3] passed
- Suite 6 (Barge-in): [X/2] passed
- Suite 7 (Calculations): [X/3] passed

## Edge Cases
- Suite 8 (Edge Cases): [X/5] passed
- Suite 9 (Multiple Sessions): [X/1] passed
- Suite 10 (Debug Panel): [X/1] passed

## Critical Issues
[List any critical bugs]

## Recommendations
[Suggestions for improvements]

## Overall Assessment
- [ ] Ready for demo
- [ ] Needs minor fixes
- [ ] Needs major fixes
```

---

## Next Steps After Testing

### If All Tests Pass:
1. Commit changes
2. Push to repository
3. Prepare demo script
4. Move to Phase 6 (Polish)

### If Some Tests Fail:
1. Document failures
2. Prioritize fixes (critical first)
3. Fix issues
4. Re-test
5. Iterate until passing

### If Major Issues Found:
1. Stop testing
2. Document all issues
3. Triage and prioritize
4. Fix critical issues first
5. Resume testing

---

**Ready to begin testing?**

Start with Test Suite 1 and work through sequentially. Good luck! 🚀
