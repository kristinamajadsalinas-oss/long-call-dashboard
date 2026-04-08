# Final Approach - Check control_frame in Real-Time

## User Requirement
**The extension should auto-reset if:**
- ❌ No more Transaction ID being detected from control_frame
- ❌ No more Call Duration being detected from control_frame

---

## How It Works

### Two Critical Moments for Checking control_frame:

#### 1. Timer Expiration (22 minutes / 1 minute in test mode)
**File:** [background.js:handleTimerExpired()](background.js)

When timer expires:
```javascript
1. Query content script: "Check control_frame RIGHT NOW"
2. Get current state:
   - transactionId: from control_frame
   - duration: from control_frame
   - isActive: (duration exists?)

3. Decision:
   ├─ No TID AND No Duration?
   │     ↓
   │  ⚠️ CALL HAS ENDED
   │     ↓
   │  Auto-reset (no template)
   │
   └─ Has TID OR Has Duration?
         ↓
      ✅ CALL IS ACTIVE
         ↓
      Show template with data
```

#### 2. X Button Clicked (User Closes Template)
**File:** [background.js:dismissCurrentCall()](background.js)

When user clicks X:
```javascript
1. Query content script: "Check control_frame RIGHT NOW"
2. Get current state from control_frame

3. Decision:
   ├─ No TID AND No Duration?
   │     ↓
   │  ✅ CALL HAS ENDED
   │     ↓
   │  Full dismissal + auto-reset
   │
   └─ Has TID OR Has Duration?
         ↓
      ⚠️ CALL STILL ACTIVE
         ↓
      Close template, keep tracking call
```

---

## control_frame States

### Active Call (control_frame has data):
```html
<div role="timer" aria-label="Interaction">07:04</div>
<li>
  <span>Transaction ID</span>
  <span title="172007">172007</span>
</li>
```
**Result:** `isActive: true`, `duration: 424`, `transactionId: '172007'`

### Call Ended (control_frame is empty):
```html
<!-- No timer element -->
<!-- No Transaction ID in list -->
```
**Result:** `isActive: false`, `duration: null`, `transactionId: null`

---

## Auto-Reset Logic

### Condition for Auto-Reset:
```javascript
const hasTransactionId = currentControlFrameState.transactionId &&
                        currentControlFrameState.transactionId !== 'Not found';
const hasCallDuration = currentControlFrameState.duration !== null;

if (!hasTransactionId && !hasCallDuration) {
  // BOTH missing from control_frame
  → Auto-reset (call has ended)
}
```

### Why BOTH Must Be Missing:
- **Transaction ID might take a moment to appear** (call just started)
- **Duration timer appears immediately** when call starts
- **If EITHER exists** → Call is active
- **If BOTH missing** → Call definitely ended

---

## Example Flows

### Flow 1: Normal Call (Template Shows)
```
[00:00] Call starts
        control_frame shows:
          Duration: 00:03
          Transaction ID: 172007

[00:03] Heartbeat sent every 3 seconds
        (continuous monitoring)

[01:00] Timer expires
        ↓
        Query control_frame RIGHT NOW:
          Duration: 01:05 ← ✅ Still there
          Transaction ID: 172007 ← ✅ Still there
        ↓
        ✅ CALL IS ACTIVE
        ↓
        Show template with TID: 172007
```

### Flow 2: Call Ended Before Timer (Auto-Reset)
```
[00:00] Call starts
        control_frame shows:
          Duration: 00:03
          Transaction ID: 172007

[00:30] User hangs up
        control_frame NOW shows:
          Duration: ❌ Gone
          Transaction ID: ❌ Gone

[01:00] Timer expires
        ↓
        Query control_frame RIGHT NOW:
          Duration: null ← ❌ Not in control_frame
          Transaction ID: null ← ❌ Not in control_frame
        ↓
        ⚠️ CALL HAS ENDED
        ↓
        Auto-reset (no template)
        Ready for next call
```

### Flow 3: X Button While Call Active
```
[01:05] Template showing
        User clicks X button
        ↓
        Query control_frame RIGHT NOW:
          Duration: 01:07 ← ✅ Still increasing
          Transaction ID: 172007 ← ✅ Still there
        ↓
        ⚠️ CALL STILL ACTIVE
        ↓
        Close template
        Keep call tracked in background
```

### Flow 4: X Button After Call Ended
```
[01:30] Template showing
        User hangs up call
        User clicks X button
        ↓
        Query control_frame RIGHT NOW:
          Duration: null ← ❌ Not in control_frame
          Transaction ID: null ← ❌ Not in control_frame
        ↓
        ✅ CALL HAS ENDED
        ↓
        Full dismissal + auto-reset
        Ready for next call
```

---

## Console Logs to Watch

### Timer Expiration - Call Active:
```
[Long Call Update] ⏰⏰⏰ TIMER EXPIRED! ⏰⏰⏰
[Long Call Update] 🔍 CHECKING control_frame for current call status...
[Long Call Update] Querying tab 123 for control_frame state...
[Long Call Update] 📊 control_frame CURRENT STATE:
  Transaction ID: 172007
  Call Duration: 1m 5s
  Is Active: ✅ YES
[Long Call Update] ✅ control_frame CONFIRMS CALL IS ACTIVE
  Transaction ID from control_frame: 172007
  Duration from control_frame: 1m 5s
[Long Call Update] ✅ Proceeding with template
```

### Timer Expiration - Call Ended:
```
[Long Call Update] ⏰⏰⏰ TIMER EXPIRED! ⏰⏰⏰
[Long Call Update] 🔍 CHECKING control_frame for current call status...
[Long Call Update] 📊 control_frame CURRENT STATE:
  Transaction ID: ❌ Not in control_frame
  Call Duration: ❌ Not in control_frame
  Is Active: ❌ NO
[Long Call Update] ⚠️⚠️⚠️ control_frame CONFIRMS CALL NOT ACTIVE - AUTO-RESETTING!
[Long Call Update] ℹ️ No Transaction ID in control_frame
[Long Call Update] ℹ️ No Call Duration in control_frame
[Long Call Update] ✅ Auto-reset complete - ready for next call
```

### X Button - Call Active:
```
[Long Call Update] 🔍 X BUTTON CLICKED - Checking control_frame...
[Long Call Update] 📊 control_frame CURRENT STATE:
  Transaction ID: 172007
  Call Duration: 1m 30s
  Is Active: ✅ YES
[Long Call Update] ⚠️ CALL IS STILL ACTIVE!
[Long Call Update] ℹ️ control_frame still shows call data
[Long Call Update] ✅ Template dismissed, call still tracked
```

### X Button - Call Ended:
```
[Long Call Update] 🔍 X BUTTON CLICKED - Checking control_frame...
[Long Call Update] 📊 control_frame CURRENT STATE:
  Transaction ID: ❌ Not in control_frame
  Call Duration: ❌ Not in control_frame
  Is Active: ❌ NO
[Long Call Update] ✅ CALL HAS ENDED
[Long Call Update] ✅ Call dismissed and removed
```

---

## Key Benefits

1. **✅ Real-Time Verification** - Always checks control_frame at critical moments
2. **✅ No False Resets** - Only resets when control_frame confirms call ended
3. **✅ No Stale Data** - Queries control_frame RIGHT NOW, not relying on old heartbeats
4. **✅ Smart X Button** - Knows if call is still active before dismissing
5. **✅ Auto-Reset Works** - No manual reloads needed
6. **✅ Source of Truth** - control_frame is the authority

---

## Testing Checklist

- [ ] Start call → Timer starts
- [ ] Wait 1 minute → Template appears with Transaction ID
- [ ] Verify TID matches what's in 8X8 control_frame
- [ ] Keep call active → Template should stay visible
- [ ] Click X while call active → Template closes, call still tracked
- [ ] Hang up call → control_frame clears
- [ ] Click X after hangup → Full dismissal + auto-reset
- [ ] Start new call → Should detect immediately (no reload)
- [ ] Hang up BEFORE 1 minute → Auto-reset at timer (no template)

---

## What Changed from Previous Version

### ❌ Before:
- Relied on heartbeat timing (could be stale)
- Used last heartbeat time to guess call state
- Could make wrong decision if heartbeat delayed

### ✅ Now:
- **Actively queries control_frame** at critical moments
- **Real-time state** from control_frame RIGHT NOW
- **Accurate decisions** based on current reality
- **Auto-reset when:** No TID AND No Duration in control_frame

---

Generated: 2026-04-06
Version: v19.5.0 (Real-Time control_frame Verification)