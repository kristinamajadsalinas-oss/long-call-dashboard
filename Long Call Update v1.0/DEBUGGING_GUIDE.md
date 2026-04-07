# Debugging Guide - Template Not Showing Issue

## Issue Description
- ✅ Call detection works
- ✅ Timer starts (1 minute in test mode)
- ❌ After 1 minute, no template appears
- ❌ Badge turns red (extension auto-resets)

## What Should Happen
1. Call detected → Badge GREEN
2. Timer runs for 1 minute
3. Timer expires → DOM verification
4. DOM confirms call active → Template appears
5. Badge stays GREEN

## Root Cause Analysis

### Possible Causes:

#### 1. DOM Verification Timeout
**Symptom:** Console shows `⚠️ DOM verification timeout (3s)`

**Cause:** Content script not responding to `VERIFY_CALL_ACTIVE` message

**Fix Applied:**
- Increased timeout from 2s to 3s
- Added defensive logic: if verification fails, show template anyway (benefit of doubt)
- Better logging to see what's happening

#### 2. Content Script Not Loaded
**Symptom:** Console shows `Failed to query DOM: Could not establish connection`

**Cause:** Content script not injected into the 8X8 tab

**Fix:** Extension should auto-inject on reload, but verify it's running

**Check:**
```javascript
// In 8X8 tab console, run:
window.longCallUpdateContentScriptLoaded
// Should return: true
```

#### 3. Wrong Tab Queried
**Symptom:** Verification returns but says `isActive: false` incorrectly

**Cause:** Querying wrong tab (not the one with active call)

**Fix Applied:**
- Better tab matching logic
- More detailed logging of which tab is being queried

---

## Console Messages to Check

### ✅ GOOD - Timer Expiration Should Show:
```
[Long Call Update] ⏰⏰⏰ TIMER EXPIRED! ⏰⏰⏰
[Long Call Update] Call ID: tab_XXX_XXXXXX
[Long Call Update] 🔍 ACTIVE DOM VERIFICATION - Querying 8X8 page...
[Long Call Update] Querying tab 123 for DOM verification...
[Long Call Update] Tab URL: https://vcc-na13.8x8.com/...
[Long Call Update] Verification took 234 ms
[Long Call Update] 📊 DOM VERIFICATION RESULT:
  Is Active: ✅ YES
  Duration: 1m 5s
  Transaction ID: 171885
[Long Call Update] ✅ DOM CONFIRMS CALL IS ACTIVE
[Long Call Update] ✅ Transaction ID updated from DOM: 171885
[Long Call Update] ✅ Call duration updated from DOM: 1m 5s
[Long Call Update] ✅ Proceeding with template (call assumed active)
[Long Call Update] Marking call as notified...
[Long Call Update] ✅✅✅ Call marked as notified! Template should appear now!
```

### ❌ BAD - If You See This:
```
[Long Call Update] ⏰⏰⏰ TIMER EXPIRED! ⏰⏰⏰
[Long Call Update] 🔍 ACTIVE DOM VERIFICATION - Querying 8X8 page...
[Long Call Update] Querying tab 123 for DOM verification...
[Long Call Update] ⚠️ DOM verification timeout (3s)
[Long Call Update] Verification took 3001 ms
[Long Call Update] ⚠️ DOM verification failed - showing template anyway (benefit of doubt)
```

### ⚠️ WARNING - Verification Failed but Template Shows Anyway:
```
[Long Call Update] ⚠️ Failed to query DOM: Could not establish connection. Receiving end does not exist.
[Long Call Update] ⚠️ DOM verification failed - showing template anyway (benefit of doubt)
[Long Call Update] ℹ️ Better to show template for active call than miss it
[Long Call Update] ✅ Proceeding with template (call assumed active)
```
**This is OKAY** - Template will still appear, just might not have Transaction ID

---

## Step-by-Step Debug Process

### Step 1: Check Extension is Loaded
1. Go to `chrome://extensions`
2. Find "Long Call Update"
3. Check "Service worker" is active (not "Inactive")
4. Click "Reload" if needed

### Step 2: Check Console Logs (Background)
1. Click "Service worker" link in extension page
2. This opens background script console
3. Make a test call
4. Watch for messages:
   - `✅ Call started - AUTOMATIC TRACKING ENABLED`
   - `Timer set for 1m 0s`
   - `⏰⏰⏰ TIMER EXPIRED!`

### Step 3: Check Console Logs (Content Script)
1. Go to 8X8 tab with active call
2. Open DevTools (F12)
3. Go to Console tab
4. Look for:
   - `Content Script v19.1.0 DURATION-BASED`
   - `✅ Call started - AUTOMATIC TRACKING ENABLED`
   - `🔍 ACTIVE DOM VERIFICATION REQUESTED` (when timer expires)

### Step 4: Manually Test Verification
In the 8X8 tab console, run:
```javascript
// Check if content script is loaded
window.longCallUpdateContentScriptLoaded

// Manually trigger verification
chrome.runtime.sendMessage({type: 'VERIFY_CALL_ACTIVE'}, (response) => {
  console.log('Verification result:', response);
});
```

Expected response:
```javascript
{
  isActive: true,
  duration: 65,  // seconds
  transactionId: "171885",
  timestamp: 1234567890
}
```

### Step 5: Check Active Calls Map
In background console:
```javascript
// Check if call is still in the map
activeCalls.size  // Should be 1 if call is active

// View all active calls
Array.from(activeCalls.entries())
```

---

## Fixed Issues

### ✅ Fix 1: Defensive Verification Logic
**Before:**
```javascript
if (!domVerification || !domVerification.isActive) {
  // Auto-reset - BAD if verification just failed!
  activeCalls.delete(callId);
}
```

**After:**
```javascript
// ONLY reset if verification EXPLICITLY says call is NOT active
if (domVerification && domVerification.isActive === false) {
  // Auto-reset - call confirmed ended
  activeCalls.delete(callId);
} else {
  // Show template anyway (verification failed or call is active)
  call.notified = true;
  showNotification(call);
}
```

**Result:** If verification times out or fails, we show template instead of auto-resetting

### ✅ Fix 2: Increased Timeout
- Increased from 2 seconds to 3 seconds
- Gives more time for content script to respond

### ✅ Fix 3: Better Logging
- Added detailed timing info
- Shows which tab is being queried
- Shows exactly what verification returned

---

## Expected Flow (With Logs)

```
[00:00] 📞 Call starts
        ✅ Call started - AUTOMATIC TRACKING ENABLED
        Transaction ID: 171885
        Timer set for 1m 0s

[00:03] 💓 Heartbeat: Call active for 0m 3s, TID: 171885
[00:06] 💓 Heartbeat: Call active for 0m 6s, TID: 171885
...

[01:00] ⏰ TIMER EXPIRED!
        🔍 Querying tab 123 for DOM verification...
        Verification took 234 ms
        📊 DOM VERIFICATION RESULT:
          Is Active: ✅ YES
          Duration: 1m 5s
          Transaction ID: 171885
        ✅ DOM CONFIRMS CALL IS ACTIVE
        ✅ Proceeding with template
        ✅✅✅ Template should appear now!
        🔔 Showing browser notification...
```

---

## Quick Test Checklist

- [ ] Extension shows in `chrome://extensions`
- [ ] Service worker is active (not "Inactive")
- [ ] Badge is GREEN when call starts
- [ ] Background console shows: `✅ Call started`
- [ ] Background console shows: `Timer set for 1m 0s`
- [ ] 8X8 tab console shows: `Content Script v19.1.0`
- [ ] After 1 minute, background console shows: `⏰ TIMER EXPIRED!`
- [ ] Background console shows: `🔍 ACTIVE DOM VERIFICATION`
- [ ] Verification completes (doesn't timeout)
- [ ] Template appears with Transaction ID filled in
- [ ] Badge stays GREEN

---

## If Template Still Doesn't Appear

### Check This in Background Console:
```javascript
// 1. Is there a notified call?
const currentCall = getCurrentCall();
console.log('Current call:', currentCall);

// 2. Check activeCalls map
console.log('Active calls:', Array.from(activeCalls.entries()));

// 3. Manually trigger notification
if (currentCall) {
  showNotification(currentCall);
}
```

### Check This in Popup:
- Open extension popup (click badge)
- Should show template with Transaction ID
- If shows "No Active Call" instead, the call was removed from activeCalls

---

## Contact Info

If issue persists, provide these logs:
1. Background console (full log from call start to 1 minute)
2. Content script console (from 8X8 tab)
3. Screenshot of `chrome://extensions` page
4. Output of `activeCalls.size` in background console after timer expires

---

Generated: 2026-04-06
Version: v19.3.1 (Defensive Verification Logic)