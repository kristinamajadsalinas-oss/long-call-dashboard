# 📞 How to Use Long Call Update Extension

## ⚡ Quick Start Guide

### First Time Setup (Do Once)

1. Click the extension icon
2. Click **"Settings"**
3. Fill in your details:
   - **Siebel ID**: Your engineer ID (e.g., kristinamajasa)
   - **Team**: Your squad name (e.g., Squad Judith)
   - **Skillset**: PS (Premium) or STD (Standard)
4. Click **"Save Settings"**

---

## 🎯 Using During Calls

### Step 1: Answer the Call (Automatic Tracking!)
- Customer calls and you answer
- **Extension automatically detects the call** ✨
- **Timer starts counting down automatically**
- No button to click - it's all automatic!

### Step 2: Wait for Notification
- Continue with your call normally
- After 22 minutes, you'll get a notification
- Click the extension icon to see the template

### Step 3: Fill the Template
1. **Copy Transaction ID from 8x8**
   - Look at your 8x8 call screen (top left)
   - Copy the Transaction ID number (e.g., 7075635508)
   - Paste it into the extension

2. **Fill in Issue**
   - Describe what problem the customer had

3. **Fill in Reason**
   - Explain why the call took so long

### Step 4: Copy & Paste to Teams
- Click **"Copy to Clipboard"**
- Open Microsoft Teams
- Paste the template
- Done! ✅

---

## 🧪 Test Mode

Want to test without waiting 22 minutes?

1. Click **"Settings"**
2. Enable **"Test mode (1-minute timer)"**
3. Click **"Save Settings"**
4. Now timers will trigger after only 1 minute!
5. **Remember to turn it OFF** when done testing

---

## 🔄 If You Started by Mistake

- Click **"Cancel & Close"** button (gray button)
- Or just close the extension popup
- Everything resets and you can start fresh

---

## 💡 Tips

✅ **Fully automatic** - Just answer calls normally, tracking starts automatically!

✅ **Keep 8x8 open** - Transaction ID is auto-detected from your call screen

✅ **Test mode is your friend** - Use 1-minute timer to practice the workflow

✅ **Always refresh 8x8** after reloading the extension for auto-detection to work

---

## ❓ Troubleshooting

**Extension says "no active calls"**
- Make sure you've **refreshed your 8x8 page** after reloading the extension
- The extension monitors your 8x8 page - it must be open
- Check console (F12) for `[Long Call Update]` messages to verify detection is working

**Transaction ID shows "Not auto-detected"**
- **Refresh your 8x8 page** (Press F5) - this is the most common fix!
- If still not detected, click "Edit" and paste it manually from your 8x8 screen
- Transaction ID is visible in the top left of your 8x8 call interface

**Timer didn't trigger after 22 minutes**
- Make sure the extension detected your call (check if you saw any tracking status)
- Check if Test Mode is enabled (should be OFF for normal 22-min tracking)
- Refresh your 8x8 page and answer another call to test
- Reload the extension: `edge://extensions/` → Click reload button

---

## 📝 Template Format

The extension creates this format:

```
TRANSACTION ID: 7075635508
SIEBEL ID: kristinamajasa
SKILLSET: PS
TEAM: Squad Judith
ISSUE: [What you type]
REASON: [What you type]
```

Copy this entire block and paste it into Teams!

---

**Need help?** Check your extension is up to date by reloading it at `edge://extensions/`
