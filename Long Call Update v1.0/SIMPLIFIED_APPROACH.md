# Simplified Approach - Use Heartbeat Data from control_frame

## Problem with Previous Approach
❌ Was trying to re-query the DOM at timer expiration
❌ Complex timeout logic and error handling
❌ Could fail if content script didn't respond

## New Simplified Approach
✅ Use data **already collected** from control_frame via heartbeats
✅ Heartbeats run every 3 seconds automatically
✅ No need to re-query - just check last heartbeat time

---

## How It Works

### Heartbeat Collection (Every 3 Seconds)
**File:** [content.js:193-206](content.js:193-206)

The content script already extracts data from control_frame:
```javascript
const currentDuration = extractCallDuration();  // From control_frame timer
const transactionId = extractTransactionId();   // From control_frame

notifyBackgroundScript('CALL_HEARTBEAT', {
  duration: currentDuration,
  transactionId: transactionId
});
```

**Console logs show this working:**
```
Check: {duration: "1m 11s", lastDuration: 69, transactionId: '172007', isActive: true}
```

### Background Script Stores This Data
**File:** [background.js:handleCallHeartbeat()](background.js)

```javascript
function handleCallHeartbeat(data, tab) {
  existingCall.callDuration = data.duration;        // ← From control_frame
  existingCall.transactionId = data.transactionId;  // ← From control_frame
  existingCall.lastSeenTime = Date.now();           // ← When we last saw it
  activeCalls.set(existingCallId, existingCall);
}
```

---

## Timer Expiration Logic (22 Minutes)

### OLD Approach (Complicated):
```javascript
❌ Query DOM again at timer expiration
❌ Wait for content script response (might timeout)
❌ Handle timeout errors
❌ Complex decision logic
```

### NEW Approach (Simple):
```javascript
✅ Check last heartbeat time
✅ If heartbeat within 15 seconds → Call is ACTIVE
✅ If no heartbeat for >15 seconds → Call has ENDED
```

**Code:**
```javascript
const timeSinceLastSeen = Date.now() - call.lastSeenTime;
const hasRecentHeartbeat = timeSinceLastSeen < 15000;

if (!hasRecentHeartbeat) {
  // No heartbeat = no duration in control_frame = call ended
  → Auto-reset
} else {
  // Recent heartbeat = call is active
  → Show template with TID from heartbeat
}
```

---

## X Button Click Logic

### OLD Approach (Complicated):
```javascript
❌ Query DOM when X clicked
❌ Wait for response
❌ Complex decision based on verification
```

### NEW Approach (Simple):
```javascript
✅ Check last heartbeat time
✅ If recent → Keep tracking (call still active)
✅ If old → Dismiss completely (call ended)
```

**Code:**
```javascript
const timeSinceLastSeen = Date.now() - currentCall.lastSeenTime;
const hasRecentHeartbeat = timeSinceLastSeen < 15000;

if (hasRecentHeartbeat) {
  // Call still active - just close template
  currentCall.notified = false;
} else {
  // Call ended - full dismissal
  activeCalls.delete(currentCall.id);
}
```

---

## Why This Is Better

### 1. **Simpler Code**
- No complex DOM queries at critical moments
- No timeout handling
- No error recovery logic

### 2. **More Reliable**
- Heartbeats already proven to work (console shows them)
- Don't depend on content script responding quickly
- Uses data we already have

### 3. **Faster**
- No need to wait for content script response
- Instant decision based on last heartbeat time
- No 2-3 second delays

### 4. **Source of Truth: control_frame**
- All data comes from control_frame (via heartbeats)
- Transaction ID from control_frame
- Duration from control_frame
- If duration exists → heartbeat sent
- If duration missing → no heartbeat

---

## Flow Diagram

```
Call Active in 8X8
    ↓
control_frame shows:
  - Duration: 1m 11s
  - Transaction ID: 172007
    ↓
[Every 3 seconds]
Content script extracts from control_frame:
  - currentDuration = extractCallDuration()  ← reads timer
  - transactionId = extractTransactionId()   ← reads TID
    ↓
Send CALL_HEARTBEAT to background:
  {duration: 71, transactionId: '172007'}
    ↓
Background stores:
  call.callDuration = 71
  call.transactionId = '172007'
  call.lastSeenTime = Date.now()
    ↓
[22 Minutes Pass - Timer Expires]
    ↓
Check last heartbeat:
  timeSinceLastSeen = now - call.lastSeenTime
    ↓
  ├─ < 15 seconds?
  │     ↓
  │  ✅ YES → Call is ACTIVE
  │     ↓
  │  Show template with:
  │    - TID: 172007 (from heartbeat)
  │    - Duration: 1m 11s (from heartbeat)
  │
  └─ > 15 seconds?
        ↓
     ❌ NO → Call has ENDED
        ↓
     Auto-reset (no reload needed)
```

---

## Call Ended Detection

### How We Know Call Ended:

**control_frame when call active:**
```html
<div role="timer">07:04</div>
<li><span>Transaction ID</span><span>172007</span></li>
```

**control_frame when call ended:**
```html
<!-- No timer element -->
<!-- No Transaction ID -->
```

**When call ends:**
1. Duration timer disappears from control_frame
2. `extractCallDuration()` returns `null`
3. No heartbeat sent (because `isActive = false`)
4. `call.lastSeenTime` becomes stale (>15 seconds old)
5. At timer expiration, no recent heartbeat detected
6. **Auto-reset!**

---

## Console Messages

### Normal Flow (Call Active):
```
[00:00] ✅ Call started - AUTOMATIC TRACKING ENABLED
        Transaction ID: 172007

[00:03] 💓 Heartbeat: Call active for 0m 3s, TID: 172007
[00:06] 💓 Heartbeat: Call active for 0m 6s, TID: 172007
...
[01:00] 💓 Heartbeat: Call active for 1m 0s, TID: 172007

[01:00] ⏰ TIMER EXPIRED!
        📊 HEARTBEAT DATA CHECK (from control_frame):
          Transaction ID: 172007
          Call Duration: 1m 5s
          Last Heartbeat: ✅ (3s ago)
        ✅ HEARTBEAT CONFIRMS CALL IS ACTIVE
        ✅ Proceeding with template
```

### Call Ended Before Timer:
```
[00:00] ✅ Call started
        Transaction ID: 172007

[00:03] 💓 Heartbeat: Call active for 0m 3s, TID: 172007
...
[00:30] 💓 Heartbeat: Call active for 0m 30s, TID: 172007

[00:35] 📴 Call ended  ← User hangs up
        ⏱️ Duration timer disappeared
        ❌ No more heartbeats sent

[01:00] ⏰ TIMER EXPIRED!
        📊 HEARTBEAT DATA CHECK:
          Last Heartbeat: ❌ (25s ago)
        ⚠️⚠️⚠️ NO RECENT HEARTBEAT - CALL ENDED - AUTO-RESETTING!
        ✅ Auto-reset complete - ready for next call
```

---

## Benefits

1. **✅ No Manual Reloads** - Auto-resets when heartbeat stops
2. **✅ Uses Existing Data** - Heartbeats already capture everything
3. **✅ Simpler Logic** - Just check last heartbeat time
4. **✅ More Reliable** - No DOM query failures
5. **✅ Faster** - No waiting for content script response
6. **✅ Source of Truth** - control_frame via heartbeats

---

## Testing Checklist

- [ ] Start call → Heartbeats appear in console every 3-6 seconds
- [ ] Heartbeats show TID and duration from control_frame
- [ ] Wait 1 minute → Template appears with TID populated
- [ ] Badge stays GREEN while call active
- [ ] Hang up before timer → Auto-reset happens (no template)
- [ ] Start another call → Detects immediately (no reload)

---

Generated: 2026-04-06
Version: v19.4.0 (Simplified - Use Heartbeat Data)