# CRITICAL FIX - Call Detection Logic

## The Problem

**Extension was detecting "calls" when there were no calls!**

### What Was Happening:
1. Agent switches to "Working Offline" mode (after break)
2. 8X8 shows timer: `17m 47s` (time in offline mode)
3. Extension detects timer → **Incorrectly thinks it's a call** ❌
4. Badge turns GREEN ❌
5. No Transaction ID found (because there's no actual call)

### Root Cause:
```javascript
// ❌ OLD LOGIC (WRONG):
if (currentDuration !== null) {
  // Duration exists → Call is active
  handleCallStart();
}
```

**Problem:** ANY timer triggered call detection:
- Break timer → Detected as "call" ❌
- Offline mode timer → Detected as "call" ❌
- Interaction history durations → Detected as "call" ❌

---

## The Solution

### Key Insight (From User):
> **"Transaction ID + Call Duration are ALWAYS together."**
> **"If there's a call duration, then there's a Transaction ID."**
> **"As long as there is a Transaction ID found in control_frame, there's an active call."**

### New Logic:
```javascript
// ✅ NEW LOGIC (CORRECT):
const hasTransactionId = transactionId &&
                        transactionId !== 'Not found' &&
                        transactionId !== 'Not detected';
const hasDuration = currentDuration !== null && currentDuration >= 0;

// ONLY detect call if BOTH exist
if (hasDuration && hasTransactionId) {
  // This is an actual call! ✅
  handleCallStart();
}
```

---

## What Changed

### Before:
```
Timer found (17m 47s)
  ↓
✅ Call detected! (WRONG)
  ↓
Badge turns GREEN
  ↓
Start tracking "call"
```

### After:
```
Timer found (17m 47s)
  ↓
Check Transaction ID: ❌ Not found
  ↓
hasTransactionId: ❌
hasDuration: ✅
bothExist: ❌ NOT A CALL
  ↓
Skip detection
  ↓
Badge stays RED
```

---

## Console Log Examples

### Working Offline (No Call):
```
[Long Call Update] 📊 Check: {
  duration: '17m 47s',
  transactionId: 'none',
  hasTransactionId: ❌,
  hasDuration: ✅,
  bothExist: ❌ NOT A CALL,
  isActive: false
}
```
**Result:** No call detected ✅

### On Break (No Call):
```
[Long Call Update] 🔍 Checking for break/AUX status in MAIN frame...
[Long Call Update] ⚠️⚠️⚠️ AGENT ON BREAK - on-break-wrapper found
[Long Call Update] ⏸️⏸️⏸️ AGENT ON BREAK - SKIPPING CALL DETECTION
```
**Result:** Detection skipped ✅

### Active Call (Real Call):
```
[Long Call Update] 📊 Check: {
  duration: '5m 30s',
  transactionId: '172196',
  hasTransactionId: ✅,
  hasDuration: ✅,
  bothExist: ✅ ACTIVE CALL,
  isActive: false
}

[Long Call Update] 🆕 NEW CALL detected!
[Long Call Update] Transaction ID: 172196
```
**Result:** Call detected ✅

### Interaction History Page (Old Data):
```
[Long Call Update] ⚠️ On excluded page: Interaction history - skipping detection
```
**Result:** Detection skipped ✅

---

## Multiple Timers in 8X8

### Timer Types:

| Timer Type | Has Transaction ID? | Should Detect as Call? |
|------------|-------------------|----------------------|
| **Active call timer** | ✅ YES | ✅ YES - Detect |
| **Break timer** | ❌ NO | ❌ NO - Skip |
| **Offline mode timer** | ❌ NO | ❌ NO - Skip |
| **Interaction history** | ❌ NO | ❌ NO - Skip (excluded page) |

### Detection Rules:

1. **Active Call:**
   - ✅ Timer exists (07:04, 22:15, etc.)
   - ✅ Transaction ID exists in control_frame
   - **Action:** Detect call, badge GREEN

2. **Working Offline:**
   - ✅ Timer exists (17m 47s)
   - ❌ No Transaction ID
   - **Action:** Skip detection, badge RED

3. **On Break:**
   - ✅ Timer exists (00:29)
   - ❌ No Transaction ID
   - ❌ `#on-break-wrapper` exists
   - **Action:** Skip detection (caught by break check), badge RED

4. **Interaction History:**
   - ✅ Past durations shown (00:01:22)
   - ❌ No current Transaction ID
   - ❌ Page title: "Interaction history"
   - **Action:** Skip detection (caught by page exclusion), badge RED

---

## Why This Fix is Critical

### Before Fix:
- ❌ False detections from offline mode
- ❌ False detections from break timers
- ❌ False detections from history pages
- ❌ Badge GREEN when no calls
- ❌ Unnecessary tracking started

### After Fix:
- ✅ Only detects actual active calls
- ✅ Requires BOTH Transaction ID AND Duration
- ✅ Badge only GREEN for real calls
- ✅ No false positives
- ✅ Clean, accurate tracking

---

## Code Changes

### File: content.js - checkCallStatus()

**Old (Wrong):**
```javascript
if (currentDuration !== null && currentDuration >= 0) {
  // Duration exists → Call is active (WRONG!)
  handleCallStart();
}
```

**New (Correct):**
```javascript
const hasTransactionId = transactionId &&
                        transactionId !== 'Not found' &&
                        transactionId !== 'Not detected';
const hasDuration = currentDuration !== null && currentDuration >= 0;

// ONLY detect if BOTH exist
if (hasDuration && hasTransactionId) {
  // Actual call! ✅
  handleCallStart();
}
```

**Also Added:**
```javascript
// Skip excluded pages
const excludedPages = [
  'Interaction history',
  'My recordings',
  'Contact Center interaction'
];

for (const excluded of excludedPages) {
  if (pageTitle.includes(excluded)) {
    return; // Skip detection
  }
}
```

---

## Testing Checklist

- [ ] On break → Badge RED (no detection)
- [ ] Working offline → Badge RED (no detection)
- [ ] Interaction history page → Badge RED (no detection)
- [ ] Start real call → Badge GREEN (detected)
- [ ] Console shows "bothExist: ✅ ACTIVE CALL"
- [ ] Real call has both TID and Duration
- [ ] Offline timer does NOT trigger detection

---

## Expected Console Logs

### ✅ Real Active Call:
```
📊 Check: {
  duration: '5m 30s',
  transactionId: '172196',
  hasTransactionId: ✅,
  hasDuration: ✅,
  bothExist: ✅ ACTIVE CALL
}
🆕 NEW CALL detected!
```

### ❌ Working Offline (Not a Call):
```
📊 Check: {
  duration: '17m 47s',
  transactionId: 'none',
  hasTransactionId: ❌,
  hasDuration: ✅,
  bothExist: ❌ NOT A CALL
}
```
No call detected message → Badge stays RED

### ❌ On Break (Not a Call):
```
⚠️⚠️⚠️ AGENT ON BREAK - on-break-wrapper found
⏸️⏸️⏸️ AGENT ON BREAK - SKIPPING CALL DETECTION
```
Detection skipped entirely → Badge stays RED

---

## Key Rule

**"Transaction ID in control_frame = Active call"**

- If Transaction ID exists → There's a call
- If no Transaction ID → No call (even if timer exists)

This is the **source of truth** for call detection!

---

Generated: 2026-04-06
Version: v20.3.0 (Critical Call Detection Fix)
