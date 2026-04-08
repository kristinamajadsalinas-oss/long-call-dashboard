# New UI Design - Single Page Layout

## Overview
Complete UI redesign to a single-page layout with better visual hierarchy and status indicators.

**IMPORTANT:** Only the UI (popup) has changed. All backend detection logic in `background.js` and `content.js` remains unchanged and working.

---

## What Changed (UI Only)

### ✅ Files Changed:
1. **popup-v2.html** - New single-page layout
2. **popup-v2.js** - New UI logic (works with existing backend)
3. **manifest.json** - Points to new popup

### ✅ Files UNCHANGED (Detection Logic):
1. **background.js** - No changes (all detection logic intact)
2. **content.js** - Only the critical fix (require both TID + Duration)
3. All message handlers remain the same
4. Timer logic unchanged
5. Badge logic unchanged
6. Persistence logic unchanged

---

## New UI Layout

### Header Section:
```
┌────────────────────────────────────────────────┐
│ [⚙]              Long Call Update Tool    [●]  │
│ Settings                                  Logo │
└────────────────────────────────────────────────┘
```

**Features:**
- **Left:** Settings gear icon (opens overlay)
- **Right:** "Long Call Update Tool" title + circular logo
- **Logo:** Gradient gray background, red circular icon

---

### Status Section:
```
┌────────────────────────────────────────────────┐
│ STATUS                                         │
│ ● Monitoring for calls...                      │
│                                                │
│ [Message box]                                  │
│ A template will appear here once you answer    │
│ a call and will notify you when you need to    │
│ update on Teams.                               │
└────────────────────────────────────────────────┘
```

**Status Indicators:**
- 🔴 **Red dot** + "No active call" (when idle)
- 🟢 **Green dot** + "Active call – duration: 5m 30s (running)" (during call)
- 🟢 **Green dot** + "Active call – 22m 5s (copy template now)" (at timer)

---

### Engineer's Info (Always Visible):
```
┌────────────────────────────────────────────────┐
│ ENGINEER'S INFO                                │
│                                                │
│ SIEBEL ID                                      │
│ [Enter your SIEBEL ID________________]         │
│                                                │
│ SQUAD                                          │
│ [Enter your SQL's name_______________]         │
│                                                │
│ SKILLSET                                       │
│ [Select skillset ▼]                            │
│  - PS (Premium)                                │
│  - STD (Standard)                              │
└────────────────────────────────────────────────┘
```

**Auto-saves** when you type or select!

---

### Template Section (Shows When Call Active):
```
┌────────────────────────────────────────────────┐
│ LONG CALL UPDATE                          [×]  │
│ ──────────────────────────────────────────     │
│                                                │
│ TRANSACTION ID                                 │
│ [172196_______________________] (read-only)    │
│                                                │
│ SIEBEL ID                                      │
│ kristinamajasa                                 │
│                                                │
│ SQUAD                                          │
│ Squad Judith                                   │
│                                                │
│ SKILLSET                                       │
│ PS                                             │
│                                                │
│ ISSUE *                                        │
│ [Describe the issue...________]                │
│                                                │
│ REASON *                                       │
│ [Explain the reason..._________]               │
│                                                │
│ ┌──────────────────────────────────────────┐  │
│ │ LONG CALL UPDATE                         │  │
│ │                                          │  │
│ │ TRANSACTION ID: 172196                   │  │
│ │ SIEBEL ID: kristinamajasa                │  │
│ │ SQUAD: Squad Judith                      │  │
│ │ SKILLSET: PS                             │  │
│ │ ISSUE: [text from above]                 │  │
│ │ REASON: [text from above]                │  │
│ └──────────────────────────────────────────┘  │
│                                                │
│ [Copy Template]                                │
└────────────────────────────────────────────────┘
```

---

### Manual Template (Bottom of Home Page):
```
+ Create Manual Template  ← Link-style button
```

---

## Backend Integration (Unchanged)

### Messages Used by New UI:

1. **GET_DEBUG_INFO** - Get active calls
   ```javascript
   const debugInfo = await chrome.runtime.sendMessage({ type: 'GET_DEBUG_INFO' });
   ```

2. **CREATE_MANUAL_TEMPLATE** - Create manual template
   ```javascript
   await chrome.runtime.sendMessage({
     type: 'CREATE_MANUAL_TEMPLATE',
     data: { transactionId: null, startTime: Date.now(), manual: true }
   });
   ```

3. **DISMISS_CALL** - Close template
   ```javascript
   await chrome.runtime.sendMessage({ type: 'DISMISS_CALL' });
   ```

4. **SETTINGS_UPDATED** - Notify settings changed
   ```javascript
   chrome.runtime.sendMessage({ type: 'SETTINGS_UPDATED' });
   ```

5. **TEMPLATE_COPIED** - Track copy action
   ```javascript
   chrome.runtime.sendMessage({ type: 'TEMPLATE_COPIED' });
   ```

**All these messages are already handled by your existing background.js!**

---

## What Still Works (Unchanged):

1. ✅ **Call detection** - content.js detects calls using Transaction ID + Duration
2. ✅ **Break detection** - Skips when `#on-break-wrapper` exists
3. ✅ **Timer logic** - 22 minutes (or 1 minute in test mode)
4. ✅ **Heartbeats** - Every 3 seconds from control_frame
5. ✅ **Auto-reset** - When no recent heartbeat
6. ✅ **Badge updates** - Red/green based on activeCalls.size
7. ✅ **Notifications** - Browser notification at timer
8. ✅ **Persistence** - Survives service worker restart
9. ✅ **Transaction ID extraction** - From control_frame
10. ✅ **All background.js logic** - Completely unchanged

---

## Only UI Changed:

### Old UI (popup.html):
- Multiple views (main, settings, tracking)
- Navigation between views
- Countdown timer
- Colorful emojis
- Complex state management

### New UI (popup-v2.html):
- Single page
- Status indicator with dots
- Settings overlay
- Clean, minimal design
- Simplified state management

**But both use the same backend!**

---

## Files Summary:

| File | Status | Notes |
|------|--------|-------|
| **background.js** | ✅ Unchanged | All detection logic intact |
| **content.js** | ✅ Working | Only has critical fix (TID+Duration required) |
| **popup-v2.html** | 🆕 New | Single-page layout |
| **popup-v2.js** | 🆕 New | New UI logic, same backend messages |
| **manifest.json** | ✅ Updated | Points to popup-v2.html |

---

## Backend Messages Flow:

```
content.js (unchanged detection)
    ↓
Detects call (TID + Duration in control_frame)
    ↓
Sends: CALL_STARTED
    ↓
background.js (unchanged)
    ↓
Stores in activeCalls, starts timer, updates badge
    ↓
popup-v2.js (new UI)
    ↓
Polls: GET_DEBUG_INFO every 3 seconds
    ↓
Shows template if activeCallsCount > 0
```

**All backend logic is the same - only the presentation layer changed!**

---

## To Verify Nothing Broke:

1. ✅ Call detection still works (TID + Duration required)
2. ✅ Break detection still works (skips when on break)
3. ✅ Timer still fires at 22 min (or 1 min)
4. ✅ Notification still appears
5. ✅ Badge still updates (red/green)
6. ✅ Template still shows
7. ✅ Copy still works
8. ✅ Manual template still works
9. ✅ Settings still save
10. ✅ Auto-reset still works

**Everything works exactly the same, just looks different!**

---

Generated: 2026-04-06
Version: v21.0.0 (New UI, Same Backend)
