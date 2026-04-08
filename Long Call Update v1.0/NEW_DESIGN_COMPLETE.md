# New Design Complete - TrendLife Branding

## Overview
Extension redesigned with TrendLife branding, version number, and single-page layout.

**CRITICAL:** Only UI changed - all backend detection logic remains unchanged and working!

---

## New Header Layout

```
┌──────────────────────────────────────────────────────┐
│ [⚙]      Long Call Update Tool          v1.0.0  [●]  │
│ Settings                                      Logo    │
└──────────────────────────────────────────────────────┘
```

**Elements:**
- **Upper Left:** Settings gear icon (solid gray glyph)
- **Center:** "Long Call Update Tool" title
- **Upper Right:** Version "v1.0.0" + Circular logo
- **Logo:** Gradient gray background with red circular icon

---

## New Footer Layout

```
┌──────────────────────────────────────────────────────┐
│                    [●] TrendLife                      │
│                 Logo + Brand Name                     │
└──────────────────────────────────────────────────────┘
```

**Elements:**
- Red circular logo (similar to header)
- "TrendLife" brand name
- Clean, minimal footer

---

## Complete Page Structure

```
┌──────────────────────────────────────────────────────┐
│ HEADER                                                │
│ [⚙]      Long Call Update Tool          v1.0.0  [●]  │
├──────────────────────────────────────────────────────┤
│                                                       │
│ STATUS                                                │
│ ● Monitoring for calls...                             │
│ [Simple message box]                                  │
│                                                       │
│ ENGINEER'S INFO                                       │
│ SIEBEL ID:  [____________]                            │
│ SQUAD:      [____________]                            │
│ SKILLSET:   [Select ▼]                                │
│                                                       │
│ [+ Create Manual Template]                            │
│                                                       │
├──────────────────────────────────────────────────────┤
│ FOOTER                                                │
│                    [●] TrendLife                      │
└──────────────────────────────────────────────────────┘
```

---

## When Call Active

```
┌──────────────────────────────────────────────────────┐
│ HEADER                                                │
│ [⚙]      Long Call Update Tool          v1.0.0  [●]  │
├──────────────────────────────────────────────────────┤
│                                                       │
│ STATUS                                                │
│ ● Active call – duration: 5m 30s (running)            │
│                                                       │
│ ENGINEER'S INFO                                       │
│ (same as above)                                       │
│                                                       │
│ LONG CALL UPDATE                              [×]     │
│ ──────────────────────────────────────────            │
│                                                       │
│ TRANSACTION ID                                        │
│ [172196________________] (auto-filled)                │
│                                                       │
│ SIEBEL ID:      kristinamajasa (auto-filled)          │
│ SQUAD:          Squad Judith (auto-filled)            │
│ SKILLSET:       PS (auto-filled)                      │
│                                                       │
│ ISSUE *                                               │
│ [Fill in_______________________________]              │
│                                                       │
│ REASON *                                              │
│ [Fill in_______________________________]              │
│                                                       │
│ [Preview box showing formatted template]              │
│                                                       │
│ [Copy Template]                                       │
│                                                       │
├──────────────────────────────────────────────────────┤
│                    [●] TrendLife                      │
└──────────────────────────────────────────────────────┘
```

---

## Settings Overlay (Gear Icon Click)

```
┌──────────────────────────────────────────────────────┐
│ Settings                                        [×]   │
├──────────────────────────────────────────────────────┤
│                                                       │
│ □ Enable test mode (1-minute timer)                  │
│                                                       │
│ DIAGNOSTICS                                           │
│ [Show Debug Info]                                     │
│ [Debug output box if clicked]                         │
│                                                       │
│ [Done]                                                │
└──────────────────────────────────────────────────────┘
```

**Features:**
- Test mode checkbox
- Debug info button
- Close button (X) or Done button

---

## Visual Design

### Color Palette:
- **Primary:** Trend Micro Red `#D71921`
- **Background:** `#F8F9FA` (light gray)
- **Cards:** `#FFFFFF` (white)
- **Borders:** `#E9ECEF`, `#DEE2E6`
- **Text:** `#212529` (dark), `#495057` (medium), `#6C757D` (light)

### Typography:
- **Header title:** 14px, weight 600
- **Section titles:** 11px, uppercase, weight 600
- **Body text:** 13px, weight 400
- **Template header:** 16px, weight 700 (bold)
- **Version:** 11px, weight 500

### Status Dots:
- **Red:** `#D71921` (no active call)
- **Green:** `#28a745` (active call)
- Size: 10px circle

### Icons:
- All solid glyph icons (SVG)
- No colorful emojis
- Gray color scheme
- Clean, minimal

---

## Backend Integration (Unchanged)

### Messages Used:
1. `GET_DEBUG_INFO` - Check for active calls (polls every 3 seconds)
2. `CREATE_MANUAL_TEMPLATE` - Create manual template
3. `DISMISS_CALL` - Close template (X button)
4. `SETTINGS_UPDATED` - Save settings
5. `TEMPLATE_COPIED` - Track copy action

### All Work With Existing background.js:
- ✅ Call detection (TID + Duration required)
- ✅ Timer (22 min or 1 min test mode)
- ✅ Heartbeats (every 3 seconds)
- ✅ Auto-reset (no heartbeat)
- ✅ Badge updates
- ✅ Notifications
- ✅ Break detection

---

## Features Preserved

### 1. Auto-Save Settings
Settings save automatically when you type or select (no save button on main page)

### 2. Template Auto-Fill
When call is detected:
- Transaction ID from control_frame
- Siebel ID from settings
- Squad from settings (auto-formatted as "Squad [name]")
- Skillset from settings

### 3. Manual Template
Click "+ Create Manual Template" to create template without active call

### 4. Live Updates
Status and duration update every 3 seconds

### 5. Test Mode
Enable in settings for 1-minute timer (instead of 22 minutes)

### 6. Debug Info
Click gear → Show Debug Info to see full state

---

## File Structure

### New Files:
- `popup-v2.html` - New single-page UI
- `popup-v2.js` - New UI logic (integrates with existing backend)

### Unchanged Files:
- `background.js` - All detection logic intact
- `content.js` - Only critical fix (TID + Duration required)
- All message handlers working
- All timer logic working
- All persistence working

### Updated Files:
- `manifest.json` - Points to popup-v2.html, version 1.0.0

---

## Branding Elements

### Header Logo:
- Circular icon with gradient gray background
- Red circular design inside
- 32px × 32px

### Footer Logo:
- Red elliptical logo (similar to TrendLife brand)
- "TrendLife" text next to logo
- Centered in footer

### Version Number:
- "v1.0.0" in upper right
- Light gray color
- Small, unobtrusive

---

## Testing Checklist

### UI Tests:
- [ ] Header shows: Gear icon, title, version, logo
- [ ] Status shows red dot when no call
- [ ] Status shows green dot when call active
- [ ] Engineer's info always visible
- [ ] Settings auto-save when typing
- [ ] Template appears when call active
- [ ] LONG CALL UPDATE header is bold and large
- [ ] Transaction ID auto-fills
- [ ] Manual template button visible when no call
- [ ] Footer shows TrendLife logo
- [ ] Settings overlay opens/closes
- [ ] Debug info works

### Backend Tests:
- [ ] Call detection still works (TID + Duration)
- [ ] Badge still updates (red/green)
- [ ] Timer still fires at 22 min
- [ ] Notification still appears
- [ ] Break detection still works
- [ ] Auto-reset still works
- [ ] Manual template still works
- [ ] Copy still works

---

## What You'll See:

### No Call:
```
┌──────────────────────────────────────────┐
│ [⚙]  Long Call Update Tool  v1.0.0  [●]  │
├──────────────────────────────────────────┤
│ STATUS                                   │
│ ● Monitoring for calls...                │
│ [Message: template will appear once...]  │
│                                          │
│ ENGINEER'S INFO                          │
│ [Your fields here]                       │
│                                          │
│ + Create Manual Template                 │
├──────────────────────────────────────────┤
│           [●] TrendLife                  │
└──────────────────────────────────────────┘
```

### Active Call:
```
┌──────────────────────────────────────────┐
│ [⚙]  Long Call Update Tool  v1.0.0  [●]  │
├──────────────────────────────────────────┤
│ STATUS                                   │
│ ● Active call – 5m 30s (running)         │
│                                          │
│ ENGINEER'S INFO                          │
│ [Your fields]                            │
│                                          │
│ LONG CALL UPDATE                    [×]  │
│ [Template with auto-filled fields]       │
│ [Copy Template]                          │
├──────────────────────────────────────────┤
│           [●] TrendLife                  │
└──────────────────────────────────────────┘
```

---

Generated: 2026-04-06
Version: v1.0.0 (TrendLife Branding + Single Page UI)
Backend: Unchanged - all detection logic working
