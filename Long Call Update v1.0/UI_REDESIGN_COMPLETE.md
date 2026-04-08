# UI Redesign - Minimal Trend Micro Palette

## Overview
The extension UI has been completely redesigned to use a minimal, clean aesthetic with only the Trend Micro color palette (no additional colors like blue, orange, pink, etc.).

---

## Color Palette Used

### Primary Colors:
- **Trend Micro Red:** `#D71921` (primary actions, branding)
- **Darker Red:** `#B8151C` (hover states)

### Neutral Grays (Minimal):
- **Background:** `#F8F9FA` (light gray)
- **White:** `#FFFFFF` (cards, inputs)
- **Borders:** `#E9ECEF`, `#DEE2E6` (subtle borders)
- **Text Dark:** `#212529` (headings, labels)
- **Text Medium:** `#495057` (body text)
- **Text Light:** `#6C757D` (secondary text)
- **Text Muted:** `#ADB5BD` (placeholders, disabled)

### ❌ Removed Colors:
- No blue (`#0066cc`)
- No orange (`#ffc107`)
- No pink/red alerts (`#ffe8e8`, `#ffcccb`)
- No green alerts (`#d4edda`, `#28a745`)
- No yellow alerts (`#fff3cd`)
- No gradients (except solid red)

---

## UI Changes Summary

### 1. X Button Spacing ✅
**Before:** Too spacious, pushed to the far right
**After:**
- Reduced padding: `4px` (was `4px 8px`)
- Smaller font: `18px` (was `20px`)
- Added `flex-shrink: 0` to prevent stretching
- Aligned with top of banner using `align-items: flex-start`

### 2. Manual Template Indicator ✅
**Added:**
```html
<span style="background: #6C757D; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 500;">
  MANUAL TEMPLATE
</span>
<span style="font-size: 11px; color: #6C757D;">Created without active call</span>
```

Shows at top of template when created via "Manual Template" button.

### 3. TEAM → SQUAD Format ✅
**Before:** Label: "TEAM", Value: "Squad Judith"
**After:** Label: "SQUAD", Value: "Squad Judith"

**Template output changed:**
```
TRANSACTION ID: 172196
SIEBEL ID: kristinamajasa
SKILLSET: PS
SQUAD: Squad Judith  ← Changed from TEAM
ISSUE: ...
REASON: ...
```

**Auto-formatting:** If user enters just "Judith", displays as "Squad Judith"

### 4. Skillset Dropdown ✅
**Already implemented correctly:**
```html
<select id="skillset">
  <option value="PS">PS (Premium)</option>
  <option value="STD">STD (Standard)</option>
</select>
```

### 5. Minimal Color Palette ✅
All UI elements updated to use only:
- Whites and grays
- Trend Micro Red for primary actions
- No additional colors

---

## Visual Changes

### Header
- **Background:** `#F8F9FA` (light gray)
- **Logo border:** `#E9ECEF` (minimal)
- **Settings icon:** Gray on white, minimal shadow
- **Title:** `#212529` (dark gray)

### Timer Info Banner
**Before Timer (Active Call):**
- **Background:** `#FFFFFF` (white)
- **Border:** `1px solid #E9ECEF`
- **Text:** `#495057` (medium gray)
- **LIVE badge:** `#6C757D` background, white text

**After Timer (Ready to Copy):**
- **Background:** `#FFFFFF` (white)
- **Border:** `1px solid #E9ECEF`
- **Text:** `#212529` (dark gray)
- **Message:** "📋 Copy and paste the template now."

### Instructions Banner
- **Background:** `#F8F9FA` (light gray)
- **Border:** `#E9ECEF`
- **Text:** `#495057` (medium gray)
- **Numbers:** `#212529` (dark gray)

### Template Fields
- **Labels:** `#6C757D` (uppercase, small)
- **Values:** `#212529` on `#F8F9FA` background
- **Inputs:** White background, `#DEE2E6` border
- **Focus:** `#ADB5BD` border, subtle gray shadow

### Buttons
**Primary (Copy):**
- **Background:** `#D71921` (Trend Micro Red)
- **Hover:** `#B8151C` (darker red)
- **Text:** White

**Secondary (Cancel, Settings):**
- **Background:** `#FFFFFF` (white)
- **Border:** `#DEE2E6` (gray)
- **Text:** `#6C757D` (medium gray)
- **Hover:** `#F8F9FA` background, `#ADB5BD` border

**Copied State:**
- **Background:** `#6C757D` (gray, not green)

### Preview Section
- **Background:** `#FFFFFF` (white)
- **Border:** `#E9ECEF`
- **Preview box:** `#F8F9FA` background
- **Text:** `#212529` (dark gray)

### No Active Call State
- **Background:** `#FFFFFF` (white card)
- **Border:** `#E9ECEF`
- **Icon:** 📞 (emoji)
- **Heading:** `#212529`
- **Text:** `#6C757D`
- **Info box:** `#F8F9FA` background

---

## Before & After Comparison

### Before (Colorful):
- 🔴 Red borders on inputs
- 🟢 Green success states
- 🟡 Yellow warning states
- 🔵 Blue info icons
- 🎨 Gradients everywhere
- 🌈 Color-coded status indicators

### After (Minimal):
- ⚪ White and light gray backgrounds
- ⬛ Dark gray text
- 🔴 Trend Micro Red only for primary actions
- 🎯 Clean, minimal borders
- 📊 Subtle shadows
- 🧼 No color coding - just clean design

---

## UI States

### State 1: No Active Call
```
┌────────────────────────────────────────┐
│         [Logo]  Long Call Update  [⚙️] │
├────────────────────────────────────────┤
│                                        │
│                   📞                   │
│          No Active Call                │
│                                        │
│    ┌────────────────────────────┐     │
│    │ Auto Tracking              │     │
│    │ • No button to click       │     │
│    │ • Starts when call answered│     │
│    │ • Template at 22 min       │     │
│    └────────────────────────────┘     │
│                                        │
│  [Manual Template]    [Settings]      │
└────────────────────────────────────────┘
```

### State 2: Active Call (Before Timer)
```
┌────────────────────────────────────────┐
│         [Logo]  Long Call Update  [⚙️] │
├────────────────────────────────────────┤
│ 📞 Active call – duration: 5m 30s     │
│ (running) [LIVE (!)]                X │
├────────────────────────────────────────┤
│ Template Ready: Transaction ID is      │
│ autofilled from the active call.       │
│                                        │
│ TRANSACTION ID:  172196  [Edit]        │
│ SIEBEL ID:       kristinamajasa        │
│ SKILLSET:        [PS (Premium) ▼]      │
│ SQUAD:           Squad Judith          │
│ ISSUE:           [Fill in]             │
│ REASON:          [Fill in]             │
│                                        │
│ Preview (Ready to Copy)                │
│ ┌────────────────────────────────┐   │
│ │ TRANSACTION ID: 172196         │   │
│ │ SIEBEL ID: kristinamajasa      │   │
│ │ SKILLSET: PS                   │   │
│ │ SQUAD: Squad Judith            │   │
│ └────────────────────────────────┘   │
│                                        │
│      [Copy]            [Cancel]        │
└────────────────────────────────────────┘
```

### State 3: Timer Reached (22 Minutes)
```
┌────────────────────────────────────────┐
│         [Logo]  Long Call Update  [⚙️] │
├────────────────────────────────────────┤
│ 📋 Copy and paste the template now.  X│
├────────────────────────────────────────┤
│ 1. Verify Transaction ID               │
│ 2. Fill Issue & Reason                 │
│ 3. Copy & paste to Teams               │
│                                        │
│ [Same template fields...]              │
│                                        │
│      [Copy]            [Cancel]        │
└────────────────────────────────────────┘
```

### State 4: Manual Template
```
┌────────────────────────────────────────┐
│         [Logo]  Long Call Update  [⚙️] │
├────────────────────────────────────────┤
│ [Manual template banner]              X│
├────────────────────────────────────────┤
│ [MANUAL TEMPLATE] Created without call │
│ 1. Enter Transaction ID manually       │
│ 2. Fill Issue & Reason                 │
│ 3. Copy & paste to Teams               │
│                                        │
│ TRANSACTION ID:  [Enter manually]      │
│ [... rest of template ...]             │
└────────────────────────────────────────┘
```

---

## Component Styling

### Buttons
```css
Primary (Copy, Manual Template):
  background: #D71921
  color: white
  border-radius: 6px
  box-shadow: 0 1px 2px rgba(0,0,0,0.08)

  Hover:
    background: #B8151C
    box-shadow: 0 2px 4px rgba(0,0,0,0.12)

Secondary (Cancel, Settings):
  background: #FFFFFF
  color: #6C757D
  border: 1px solid #DEE2E6
  border-radius: 6px

  Hover:
    background: #F8F9FA
    border-color: #ADB5BD
```

### Cards/Sections
```css
background: #FFFFFF
border: 1px solid #E9ECEF
border-radius: 8px (or 6px for smaller elements)
box-shadow: 0 1px 2px rgba(0,0,0,0.04)
```

### Text Hierarchy
```css
Headings: #212529 (dark gray)
Body text: #495057 (medium gray)
Secondary text: #6C757D (light gray)
Placeholders: #ADB5BD (muted gray)
```

---

## All Changes Made

### popup.html:
- ✅ Updated all color values to minimal palette
- ✅ Removed gradients (except solid red for buttons)
- ✅ Changed border-radius to consistent values (6px/8px)
- ✅ Minimal shadows (0 1px 2px)
- ✅ Fixed X button spacing
- ✅ Changed TEAM label to SQUAD

### popup.js:
- ✅ Updated all inline styles to minimal colors
- ✅ Removed color-coded status indicators
- ✅ Added MANUAL TEMPLATE badge
- ✅ Updated LIVE CALL DATA badge (gray, not red)
- ✅ Auto-format team as "Squad [name]"
- ✅ Changed SQUAD in template output
- ✅ Removed color parameters from functions

---

## Trend Micro Brand Compliance

### ✅ Using Trend Micro Red:
- Primary action buttons (Copy, Manual Template, Save Settings)
- Logo/branding elements
- Emphasis text (only where needed)

### ✅ Minimal Design:
- Clean white cards
- Subtle gray borders
- Minimal shadows
- No unnecessary colors
- Consistent spacing
- Professional appearance

### ✅ No Extra Colors:
- No blue info indicators
- No green success states
- No yellow warnings
- No orange accents
- No pink/red backgrounds

---

## Testing Checklist

Visual inspection:
- [ ] Header is white/gray (no colors)
- [ ] Timer banner is white with gray text
- [ ] LIVE badge is gray (not red/orange)
- [ ] Template fields are white/light gray
- [ ] Input borders are gray (not red)
- [ ] Copy button is Trend Micro Red only
- [ ] Cancel button is white/gray
- [ ] No colored success/warning messages
- [ ] Settings page is all white/gray
- [ ] Manual template indicator is gray
- [ ] X button is properly positioned

Functionality:
- [ ] All buttons work
- [ ] Skillset dropdown has both options
- [ ] SQUAD shows "Squad [name]" format
- [ ] Template output shows SQUAD not TEAM
- [ ] LIVE indicator tooltip works
- [ ] X button closes template properly

---

## Files Modified

1. **popup.html** - Complete color palette update
2. **popup.js** - Updated inline styles and logic

---

Generated: 2026-04-06
Version: v20.1.0 (Minimal Trend Micro Design)
