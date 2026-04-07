# 🔍 Fully Automatic Call Tracking

## ✅ How Automatic Tracking Works

The extension is **fully automatic**! You don't need to click any buttons or manually copy-paste anything.

### What the Extension Does Automatically:

1. **Watches your 8x8 page** continuously
2. **Detects when a call starts** automatically - no button needed!
3. **Starts the timer** immediately (22 min or 1 min in test mode)
4. **Scans the page** for the Transaction ID number
5. **Extracts the ID** (e.g., 7075635508) from the interface
6. **Auto-fills it** in the template when time is up

---

## 🚀 Setup for Auto-Detection to Work

### IMPORTANT: You MUST do this for auto-detection to work!

#### **Step 1: Reload the extension**
1. Go to `edge://extensions/`
2. Find **"Long Call Update Assistant"**
3. Click the **reload button** (🔄)

#### **Step 2: Refresh your 8x8 page** ⚠️ CRITICAL!
1. Go to your 8x8 tab: `https://vcc-na13.8x8.com/...`
2. Press **F5** or click the refresh button
3. **Log back in if needed**

**Why?** The extension can only monitor pages that load AFTER the extension is installed. If you installed/reloaded the extension, you MUST refresh the 8x8 page for auto-detection to work!

---

## 🧪 Testing Auto-Detection

### Test 1: Check if content script is loaded

1. Open your 8x8 page
2. Press **F12** to open Developer Tools
3. Click **Console** tab
4. Look for this message:
   ```
   [Long Call Update] Content script loaded on 8x8 VCC
   [Long Call Update] URL: https://vcc-na13.8x8.com/...
   [Long Call Update] Initializing 8x8 integration...
   ```

✅ **If you see this** - auto-detection is active!
❌ **If you DON'T see this** - refresh the page!

### Test 2: Test automatic call tracking

1. **Answer a customer call** (or be on an active call)
2. **Check extension icon** - you may see a countdown badge
3. **Open the extension popup** - you should see "Call Timer Active" with countdown
4. **Wait for the template** (1 min in test mode, 22 min in normal mode)
5. **Check the Transaction ID field:**
   - 🟢 **Green background** = Auto-detected! ✅
   - 🟡 **Yellow background** = Not detected, click "Edit" to enter manually

---

## 🔧 Troubleshooting Auto-Detection

### Problem: Transaction ID shows "Not auto-detected"

**Solution 1: Refresh 8x8 page**
- The most common issue is forgetting to refresh the 8x8 page after reloading the extension
- Press F5 on your 8x8 tab

**Solution 2: Check console**
- Open Developer Tools (F12) → Console tab
- Look for `[Long Call Update]` messages
- You should see detection attempts

**Solution 3: Try manual detection**
- Click the **"Edit"** button next to Transaction ID
- Paste it manually from your 8x8 screen

**Solution 4: Verify you're on the right page**
- URL must be `https://vcc-na13.8x8.com/*`
- If your 8x8 uses a different URL, let me know!

---

## 📋 Manual Override (Backup Option)

Even with auto-detection, you can always manually edit:

1. When template appears, look at Transaction ID field
2. If it shows the wrong number (or says "Not auto-detected")
3. Click **"Edit"** button
4. Paste the correct Transaction ID from your 8x8 screen

---

## 🎯 Expected Behavior

### ✅ Working Correctly:

**When you start a call:**
```
[Console] [Long Call Update] Call started
[Console] [Long Call Update] Transaction ID found via number scan: 7075635508
```

**When template appears:**
- Transaction ID field shows the number with a **green background**
- You only need to fill Issue and Reason
- Click Copy and paste to Teams!

### ❌ Not Working:

**Console shows:**
```
[Console] [Long Call Update] No Transaction ID found
```

**Template shows:**
- Transaction ID field is **yellow** and says "Not auto-detected"
- Manual input field appears
- You need to paste it manually

**Fix:** Refresh your 8x8 page!

---

## 💡 Pro Tips

✅ **Always refresh 8x8** after reloading the extension

✅ **Check console logs** if auto-detection isn't working

✅ **Test mode is your friend** - use 1-minute timer to test quickly

✅ **Manual override always works** - if auto-detection fails, click "Edit"

✅ **Report issues** - if a specific 8x8 page layout doesn't work, take a screenshot!

---

## 🔬 Advanced: How Detection Works

The extension uses multiple detection methods:

1. **Specific selectors** - looks for elements with IDs/classes containing "transaction", "interaction", etc.
2. **Text patterns** - searches for "Transaction ID: 12345" in the page text
3. **Label-value pairs** - finds labels like "Transaction ID" and reads the next element
4. **Number scanning** - looks for 8-10 digit numbers anywhere on the page (like 7075635508)

It tries ALL methods and returns the first valid Transaction ID found!

---

**Remember: Refresh your 8x8 page after reloading the extension!** 🔄
