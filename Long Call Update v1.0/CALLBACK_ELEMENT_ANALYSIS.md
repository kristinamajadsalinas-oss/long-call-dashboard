# Callback HTML Element Analysis

## Overview
Analysis of the 8X8 callback (outbound call) HTML element showing what data is available during a callback interaction.

---

## Available Data in Callback Element

### 1. Customer Information
**Customer Name:** `Gracielle Amelie Narvaez`

**Found in:**
```html
<h1 title="Gracielle Amelie Narvaez"
    aria-label="Find matches for Gracielle Amelie Narvaez"
    data-test-id="active-call-name">
  Gracielle Amelie Narvaez
</h1>
```

**Also in avatar:**
```html
<div role="img" aria-label="Gracielle Amelie Narvaez">
  GA  <!-- Initials -->
</div>
```

---

### 2. Call Duration Timer
**Duration:** `04:16` (4 minutes 16 seconds)

**Found in:**
```html
<div aria-live="off"
     role="timer"
     aria-label="Interaction"
     data-test-id="interaction-timer"
     data-id="interaction-timer">
  04:16
</div>
```

**Format:** MM:SS
**Updates:** Every second
**This is the CALL DURATION** (not customer wait time)

---

### 3. Transaction ID
**Transaction ID:** `172866`

**Found in Info Tab:**
```html
<li>
  <span>Transaction ID</span>
  <div>
    <span title="172866">172866</span>
  </div>
</li>
```

**Location:** Info tab → Transaction ID field

---

### 4. Agent Status
**Status:** `Busy` (on call)
**Status Duration:** `4m 21s` (how long in Busy state)

**Found in:**
```html
<div data-test-id="user-status" data-status-value="Busy">
  <div aria-label="Busy" role="img">
    <!-- Red circle indicator -->
  </div>
</div>

<div role="timer"
     aria-label="Busy for 4 minutes 21 seconds"
     data-test-id="user-presence-timer">
  4m 21s
</div>
```

---

### 5. Call Quality Indicator
**Quality:** `Good`
**Color:** Green (#127440)

**Found in:**
```html
<button data-test-id="call-quality-badge"
        color="#127440"
        aria-label="Connection quality is good">
</button>
```

**Possible values:**
- Good (green)
- Average (yellow/orange)
- Poor (red)

---

### 6. Call Control Buttons Available

**Buttons Present:**
1. **Mute** - `data-test-id="mute-button"`
2. **Hold** - `data-test-id="hold-button"`
3. **Dialpad** - `data-test-id="dialpad-button"`
4. **Add Participant** - `data-test-id="add-participant-button"`
5. **Hang Up** - `data-test-id="hangup-button"`

---

### 7. Available Tabs
1. **Info** - Selected (showing customer and transaction info)
2. **Notes** - For agent notes
3. **Disposition** - For call categorization

---

### 8. Agent Session Information (from config)

**Agent:**
- Username: `agTsMgSUN6Tm65K_HLjJlHGg`
- GUID: `trendmicroworld01-agTsMgSUN6Tm65K_HLjJlHGg-a94515af-1ca2-4aba-8c33-bc1cc2ae88e0`
- Login ID: `kristinamaja_salinas@trendmicro.com`

**Tenant:**
- Tenant ID: `trendmicroworld01`
- Platform: `vcc-na13.8x8.com`
- Cluster: `na13`

**Session:**
- Session ID: `de3dfd2287dc97002cce8ea22276450f-75414762`
- SID: `RjuP79zujZz0LP328nIMwbspihSw9NFA`

---

## Comparison: Callback vs Inbound Call

### Similarities (Both Have):
- ✅ Call duration timer (`interaction-timer`)
- ✅ Transaction ID (in Info tab)
- ✅ Call control buttons (Mute, Hold, Hang up, etc.)
- ✅ Call quality indicator
- ✅ Info/Notes/Disposition tabs
- ✅ Agent status indicator

### Differences:

| Feature | Inbound Call | Callback (Outbound) |
|---------|-------------|---------------------|
| **Header Display** | Phone number (e.g., +64272210443) | Customer name (Gracielle Amelie Narvaez) |
| **Queue** | ✅ Shown (e.g., "OB Consumer") | ❌ Not shown in this element |
| **Wait Time** | ✅ Shown (e.g., "00:00") | ❌ Not shown in this element |
| **Phone Number** | In header + Info tab | Not visible in this element |
| **Customer Name** | Not shown | ✅ In header + avatar |
| **Avatar** | User icon | Customer initials (GA) |

---

## Key Detection Points for Extension

### To Detect Active Callback:

1. **Call Duration Timer:**
   ```javascript
   const callTimer = document.querySelector('[data-test-id="interaction-timer"]');
   // Returns: "04:16"
   ```

2. **Transaction ID:**
   ```javascript
   // In Info tab, look for <li> with "Transaction ID"
   const tidElement = Array.from(document.querySelectorAll('li'))
     .find(li => li.textContent.includes('Transaction ID'));
   // Extract: "172866"
   ```

3. **Customer Name (Callback specific):**
   ```javascript
   const customerName = document.querySelector('[data-test-id="active-call-name"]');
   // Returns: "Gracielle Amelie Narvaez"
   ```

### What's NOT Available:
- ❌ Phone number (not shown in callback UI)
- ❌ Queue name
- ❌ Wait time
- ❌ Direction indicator (inbound vs outbound)

---

## Extension Behavior with Callbacks

### Current Detection Logic Works:
```javascript
// Check 1: Has call duration timer?
const callDuration = extractCallDuration(); // "04:16" → 256 seconds

// Check 2: Has Transaction ID?
const transactionId = extractTransactionId(); // "172866"

// Decision:
if (callDuration && transactionId) {
  // ✅ Active callback detected!
  // Start tracking, show template
}
```

### Template Will Show:
```
LONG CALL UPDATE

TRANSACTION ID: 172866
SIEBEL ID: kristinamajasa
SQUAD: Squad Judith
SKILLSET: PS
ISSUE: [Fill in]
REASON: [Fill in]
```

**Works the same for both inbound and callback!**

---

## Info Tab Contents (Callback)

```html
<ul>
  <li>
    <span>Customer</span>
    <span title="Gracielle Amelie Narvaez">Gracielle Amelie Narvaez</span>
  </li>
  <li>
    <span>Transaction ID</span>
    <span title="172866">172866</span>
  </li>
</ul>
```

**Available:**
- ✅ Customer name
- ✅ Transaction ID

**Not shown (in this callback):**
- Phone number
- Queue
- Wait time

---

## Visual Indicators

### Header:
- Customer name in large text
- Call duration timer
- Call quality badge (green = good)

### Avatar:
- Customer initials: "GA"
- Different from inbound (which shows user icon)

### Status:
- Agent status: "Busy" (red indicator)
- Status timer: "4m 21s"

---

## Callback vs Inbound Summary

### For Extension Detection:
**Both types have the SAME critical elements:**
1. ✅ `[data-test-id="interaction-timer"]` - Call duration
2. ✅ Transaction ID in Info tab
3. ✅ `[data-test-id="phone-card-test-id"]` - Phone card container

**Extension detects both the same way:**
- Check for interaction-timer
- Extract Transaction ID
- If both exist → Active call (regardless of inbound/callback)

### Visual Differences:
**Inbound:**
- Shows: Phone number
- Header: +64272210443
- Info tab: Phone number, Queue, Wait time, Transaction ID

**Callback:**
- Shows: Customer name
- Header: Gracielle Amelie Narvaez
- Info tab: Customer, Transaction ID

---

## Important for Extension

### ✅ What Works the Same:
- Call detection (both have interaction-timer + Transaction ID)
- Duration extraction
- Transaction ID extraction
- Template generation
- Copy to clipboard

### ⚠️ What's Different:
- Header display (phone number vs customer name)
- Info tab contents (different fields)
- But extension doesn't need these - only needs TID!

---

## Conclusion

**Your extension will work perfectly with callbacks!**

The extension only needs:
1. Call duration timer (`interaction-timer`) ✅
2. Transaction ID (in Info tab) ✅

Both are present in callbacks, so detection, tracking, and template generation will work identically for both inbound calls and callbacks!

---

Generated: 2026-04-06
Type: Callback (Outbound) Call Analysis
Customer: Gracielle Amelie Narvaez
Transaction ID: 172866
Duration: 04:16
