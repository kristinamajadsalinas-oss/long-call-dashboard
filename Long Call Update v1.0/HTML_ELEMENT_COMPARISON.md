# HTML Element Comparison: On Break vs Active Call

## Overview
Comparison of the two different 8X8 UI states and what data is available in each.

---

## 1. ON BREAK HTML Element

### Container:
```html
<div id="on-break-wrapper" class="...">
```

### Key Elements:

#### Break Status Heading:
```html
<h1>On Break for:</h1>
```

#### Break Timer:
```html
<div role="timer"
     id="timeCounter"
     data-test-id="on-break-timer"
     data-id="on-break-timer">
  00:29
</div>
```
- Shows how long agent has been on break
- Updates every second (countdown or count-up)

#### Break Reason:
```html
<span title="Restroom">Restroom</span>
```
- Shows why agent is on break
- Examples: Restroom, Lunch, Break, etc.

#### Ready to Work Button:
```html
<button data-test-id="on-break-page-button-ready-to-work"
        data-id="on-break-page-button-ready-to-work"
        title="Ready to work">
  Ready to work
</button>
```
- When visible, indicates agent is NOT available for calls
- Click to return to available status

#### Status Menu:
```html
<button aria-pressed="true"
        aria-label="Break"
        data-test-value="onBreak">
  Break
</button>

<button aria-pressed="false"
        aria-label="Work Offline"
        data-test-value="workOffline">
  Work Offline
</button>
```

#### Decorative SVG:
- Illustration of person on break (lunch/coffee scene)
- Visual indicator of break status

### ❌ What's NOT Available on Break:
- No call duration timer
- No Transaction ID
- No phone number
- No call control buttons (Mute, Hold, Hang up, etc.)
- No Info/Notes/Disposition tabs
- No call quality indicator

---

## 2. ON CALL (Active Call) HTML Element

### Container:
```html
<main aria-label="Agent Workspace Control Panel">
  <div data-test-id="phone-card-test-id">
```

### Key Elements:

#### Phone Number Display:
```html
<h1 title="+64272210443"
    data-test-id="active-call-name">
  +64272210443
</h1>
```

#### Call Duration Timer:
```html
<div role="timer"
     aria-label="Interaction"
     data-test-id="interaction-timer"
     data-id="interaction-timer">
  07:04
</div>
```
- Shows call duration in MM:SS or H:MM:SS format
- Updates every second
- **Key indicator that a call is active**

#### Call Quality Badge:
```html
<button data-test-id="call-quality-badge"
        aria-label="Connection quality is good">
```
- Shows connection quality (Good/Average/Poor)

#### Call Control Buttons:
1. **Mute** (`data-test-id="mute-button"`)
2. **Hold** (`data-test-id="hold-button"`)
3. **Record** (`data-test-id="record-button"`)
4. **Dialpad** (`data-test-id="dialpad-button"`)
5. **Transfer** (`data-test-id="transfer-button"`)
6. **Add Participant** (`data-test-id="add-participant-button"`)
7. **Hang Up** (`data-test-id="hangup-button"`)

#### Info Tab Content:
```html
<ul>
  <li>
    <span>Phone number</span>
    <span title="+64272210443">+64272210443</span>
  </li>
  <li>
    <span>Queue</span>
    <span title="OB Consumer">OB Consumer</span>
  </li>
  <li>
    <span>Wait time</span>
    <span title="00:00">00:00</span>
  </li>
  <li>
    <span>Transaction ID</span>
    <span title="49991">49991</span>
  </li>
</ul>
```

#### Available Tabs:
1. **Info** - Call details (phone, queue, wait time, Transaction ID)
2. **Notes** - Agent notes during call
3. **Disposition** - Call categorization

### ❌ What's NOT Available During Active Call:
- No break wrapper
- No "Ready to work" button
- No break timer
- No break reason display

---

## Key Differences Summary

| Feature | On Break | Active Call |
|---------|----------|-------------|
| **Container ID** | `#on-break-wrapper` | `data-test-id="phone-card-test-id"` |
| **Timer Element** | `data-test-id="on-break-timer"` | `data-test-id="interaction-timer"` |
| **Timer Shows** | Break duration | Call duration |
| **Phone Number** | ❌ Not shown | ✅ Shown in header + Info tab |
| **Transaction ID** | ❌ Not available | ✅ Available in Info tab |
| **Queue** | ❌ Not shown | ✅ Shown (e.g., "OB Consumer") |
| **Wait Time** | ❌ Not shown | ✅ Shown (e.g., "00:00") |
| **Call Controls** | ❌ None | ✅ Mute, Hold, Record, etc. |
| **Ready to Work Button** | ✅ Shown | ❌ Not shown |
| **Status** | "On Break for:" heading | Phone number heading |
| **Reason/Label** | Break reason (Restroom, Lunch) | Queue name (OB Consumer) |

---

## Detection Logic for Extension

### To Detect "On Break" Status:
```javascript
// Method 1: Check for break wrapper (most reliable)
const onBreakWrapper = document.getElementById('on-break-wrapper');

// Method 2: Check for Ready to work button
const readyButton = document.querySelector('[data-test-id="on-break-page-button-ready-to-work"]');

// Method 3: Check for break timer
const breakTimer = document.querySelector('[data-test-id="on-break-timer"]');

// Method 4: Check for "On Break for:" heading
const breakHeading = document.querySelector('h1');
if (breakHeading?.textContent.includes('On Break for')) {
  // Agent is on break
}
```

### To Detect "Active Call":
```javascript
// Method 1: Check for interaction timer (call duration)
const callTimer = document.querySelector('[data-test-id="interaction-timer"]');

// Method 2: Check for Transaction ID in Info tab
const transactionIdElement = Array.from(document.querySelectorAll('li'))
  .find(li => li.textContent.includes('Transaction ID'));

// Method 3: Check for phone card
const phoneCard = document.querySelector('[data-test-id="phone-card-test-id"]');

// Call is active if ANY of these exist
```

---

## Data Extraction by State

### From On Break HTML:
```javascript
{
  status: "On Break",
  breakDuration: "00:29",  // From on-break-timer
  breakReason: "Restroom",  // From span title
  canTakeCalls: false,
  hasActiveCall: false
}
```

### From Active Call HTML:
```javascript
{
  status: "On Call",
  phoneNumber: "+64272210443",
  callDuration: "07:04",      // From interaction-timer
  transactionId: "49991",     // From Info tab
  queue: "OB Consumer",       // From Info tab
  waitTime: "00:00",          // From Info tab
  hasActiveCall: true,
  canTakeCalls: false  // Already on a call
}
```

---

## Why This Matters for the Extension

### Scenario 1: Agent on Break
```
8X8 Page State:
  ✅ #on-break-wrapper exists
  ✅ "Ready to work" button visible
  ✅ Break timer showing
  ❌ NO interaction-timer
  ❌ NO Transaction ID

Extension Behavior:
  ⏸️ Skip call detection
  ⚫ Badge stays RED
  📝 Don't track any calls
```

### Scenario 2: Agent on Active Call
```
8X8 Page State:
  ❌ NO on-break-wrapper
  ❌ NO "Ready to work" button
  ✅ interaction-timer showing (07:04)
  ✅ Transaction ID in Info tab (49991)
  ✅ Call control buttons visible

Extension Behavior:
  ✅ Detect call
  🟢 Badge turns GREEN
  📊 Extract Transaction ID
  ⏱️ Start tracking duration
  📋 Show template immediately
```

---

## HTML Structure Breakdown

### On Break Structure:
```
on-break-wrapper
  └── Inner container
      ├── h1: "On Break for:"
      ├── Timer div (data-test-id="on-break-timer"): "00:29"
      ├── Break reason span: "Restroom"
      ├── SVG illustration
      └── Buttons
          ├── "Ready to work" button
          └── Status menu
              ├── Break (selected)
              └── Work Offline
```

### Active Call Structure:
```
phone-card-test-id
  ├── Header
  │   ├── Phone number h1: "+64272210443"
  │   ├── Call timer (data-test-id="interaction-timer"): "07:04"
  │   └── Call quality badge
  ├── Call control buttons
  │   ├── Mute, Hold, Record
  │   ├── Dialpad, Transfer, Add participant
  │   └── Hang up
  └── Tabs
      ├── Info (selected)
      │   └── List
      │       ├── Phone number: "+64272210443"
      │       ├── Queue: "OB Consumer"
      │       ├── Wait time: "00:00"
      │       └── Transaction ID: "49991"
      ├── Notes
      └── Disposition
```

---

## Test IDs for Extension Detection

### On Break State:
- `#on-break-wrapper` - Main container
- `[data-test-id="on-break-timer"]` - Break timer
- `[data-test-id="on-break-page-button-ready-to-work"]` - Ready button
- `[data-test-value="onBreak"]` - Break status indicator

### Active Call State:
- `[data-test-id="phone-card-test-id"]` - Phone card
- `[data-test-id="interaction-timer"]` - Call duration timer
- `[data-test-id="active-call-name"]` - Phone number
- `[data-test-id="info-tab_TAB"]` - Info tab
- Transaction ID is in `<ul>` list within Info tab

---

## Extension Logic

### Current Detection Flow:
```javascript
1. Check if on break (main frame only):
   if (#on-break-wrapper exists) {
     → Skip call detection
     → Clear any tracked calls
     → Keep badge RED
     → Return early
   }

2. If not on break, check for active call:
   currentDuration = extractCallDuration()  // interaction-timer
   transactionId = extractTransactionId()   // Info tab

   if (currentDuration exists) {
     → Call is active
     → Badge GREEN
     → Track call
     → Show template
   }
```

---

## Visual Differences

### On Break Screen:
- Large break timer in center
- "On Break for:" heading
- Illustration/artwork
- "Ready to work" blue button
- No call controls
- No phone number
- Minimal UI focused on break status

### Active Call Screen:
- Phone number as header
- Call timer in top section
- Call control buttons (7 buttons)
- Info tabs at bottom
- Transaction ID in Info tab
- Full call workspace UI
- Busy/active interface

---

Generated: 2026-04-06
Purpose: Documentation of 8X8 UI states for extension detection logic
