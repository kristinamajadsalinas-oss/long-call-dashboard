# Long Call Update Assistant

A browser extension that automatically helps engineers create long call update templates when calls reach 22 minutes.

## Features

- **Automatic Call Detection**: Monitors 8x8 VCC interface and detects when calls start
- **22-Minute Timer**: Automatically tracks call duration and notifies at 22 minutes
- **Auto-Population**: Pre-fills Transaction ID, SIEBEL ID, SKILLSET, and TEAM
- **Easy Copy-Paste**: One-click copy to clipboard for pasting into Teams
- **Configurable Settings**: Set your engineer details once and reuse
- **Test Mode**: Developer mode with 1-minute timer for testing

## Installation

### Step 1: Generate Icons

Before installing, you need to create the required icon files:

1. Open `icons/generate-icons.html` in your browser
2. Right-click each generated icon and "Save image as..."
3. Save them in the `icons/` directory as:
   - `icon16.png`
   - `icon48.png`
   - `icon128.png`

See `icons/README.txt` for alternative methods.

### Step 2: Install Extension

#### For Google Chrome:

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Select the "Long Call Update" folder
5. The extension should now appear in your extensions list

#### For Microsoft Edge:

1. Open Edge and navigate to `edge://extensions/`
2. Enable "Developer mode" (toggle in bottom-left)
3. Click "Load unpacked"
4. Select the "Long Call Update" folder
5. The extension should now appear in your extensions list

### Step 3: Configure Settings

1. Click the extension icon in your browser toolbar
2. Click "Configure Settings" or right-click the extension icon and select "Options"
3. Fill in your details:
   - **SIEBEL ID**: Your unique SIEBEL identifier (e.g., kristinamajasa)
   - **TEAM**: Your team name (e.g., Squad *team name*)
   - **Default SKILLSET**: Select PS (Premium) or STD (Standard)
4. Click "Save Settings"

**Optional**: Enable "Test mode" for testing with a 1-minute timer instead of 22 minutes.

## Usage

### Normal Operation:

1. **Log into 8x8**: Open the 8x8 VCC interface at `https://vcc-na13.8x8.com`
2. **Take a Call**: When you receive a call, the extension automatically detects it
3. **Timer Starts**: The extension begins tracking the call duration
4. **22-Minute Notification**: When the call reaches 22 minutes:
   - You'll receive a browser notification
   - Extension icon shows a red badge (!)
5. **Open Template**: Click the notification or extension icon to open the template
6. **Fill Details**:
   - Transaction ID, SIEBEL ID, SKILLSET, and TEAM are auto-filled
   - Manually enter ISSUE and REASON
7. **Copy to Teams**: Click "Copy to Clipboard" button
8. **Paste in Teams**: Paste the template into your Teams message

### Template Format:

The extension generates the following format:

```
TRANSACTION ID: 62371
SIEBEL ID: kristinamajasa
SKILLSET: PS
TEAM: Squad *team name*
ISSUE: [Your issue description]
REASON: [Your reason for long call]
```

## Troubleshooting

### Extension doesn't detect calls:

**Problem**: The extension isn't detecting when calls start in 8x8.

**Solutions**:
1. Make sure you're on the correct 8x8 URL: `https://vcc-na13.8x8.com`
2. Check browser console (F12 → Console tab) for log messages starting with `[Long Call Update]`
3. Look for any error messages

### Transaction ID not found:

**Problem**: Transaction ID shows as "Not found" in the template.

**Solutions**:
1. The extension uses multiple methods to find the Transaction ID
2. If it's not detecting automatically, you may need to customize the DOM selectors
3. To debug:
   - Open the 8x8 interface during a call
   - Press F12 to open Developer Tools
   - In the Elements tab, locate the Transaction ID on the page
   - Note the element's class, id, or other attributes
   - Contact the developer to add specific selectors for your 8x8 configuration

### Settings not saving:

**Problem**: Settings don't persist after closing the browser.

**Solutions**:
1. Make sure you clicked "Save Settings" button
2. Check if you have sufficient browser permissions
3. Try disabling and re-enabling the extension
4. Reinstall the extension if problem persists

### Notification doesn't appear:

**Problem**: No notification at 22 minutes.

**Solutions**:
1. Check browser notification permissions:
   - Chrome: Settings → Privacy and security → Site Settings → Notifications
   - Edge: Settings → Cookies and site permissions → Notifications
2. Make sure notifications are allowed for Chrome/Edge
3. Check if extension is still running (icon should show in toolbar)

## Developer Mode

Enable "Test mode" in settings to use a 1-minute timer instead of 22 minutes. This is useful for:
- Testing the extension without waiting 22 minutes
- Verifying the installation works correctly
- Debugging issues

**Important**: Remember to disable test mode for actual production use!

## Advanced Configuration

### Custom DOM Selectors:

If the extension isn't detecting the Transaction ID, you can customize the selectors:

1. Open `content.js` in a text editor
2. Find the `CONFIG` object at the top
3. Modify the `transactionIdSelectors` array to add your specific selectors
4. Reload the extension in Chrome/Edge

Example:
```javascript
transactionIdSelectors: [
  '#your-custom-id',
  '.your-custom-class',
  '[data-your-attribute]'
]
```

### Changing Timer Duration:

To modify the notification time (currently 22 minutes):

1. Open `background.js`
2. Find the line: `const NOTIFICATION_TIME_MS = 22 * 60 * 1000;`
3. Change `22` to your desired number of minutes
4. Reload the extension

## Privacy & Security

- **Local Storage Only**: All data is stored locally in your browser using Chrome's storage API
- **No External Servers**: No data is sent to external servers
- **No Tracking**: The extension doesn't track or collect any analytics
- **8x8 Integration**: Only accesses the 8x8 VCC interface you're logged into
- **Teams Integration**: Copy-paste only, no direct Teams integration

## Technical Details

### Files:

- `manifest.json` - Extension configuration (Manifest V3)
- `background.js` - Background service worker for timer management
- `content.js` - Content script for 8x8 integration
- `popup.html/js` - Template popup interface
- `options.html/js` - Settings configuration page
- `styles.css` - Shared styling

### Permissions:

- `storage` - Save user settings and call data
- `notifications` - Show 22-minute notifications
- `alarms` - Timer functionality
- `activeTab` - Access current tab
- `https://vcc-na13.8x8.com/*` - Access 8x8 interface

### Browser Compatibility:

- ✅ Google Chrome (Manifest V3)
- ✅ Microsoft Edge (Manifest V3)
- ❌ Firefox (requires Manifest V2 adaptation)
- ❌ Safari (requires different approach)

## Known Limitations

1. **8x8 DOM Changes**: If 8x8 updates their interface, the Transaction ID detection may stop working
2. **Single Tab**: Only tracks calls in the 8x8 tab where the extension is active
3. **Page Refresh**: If you refresh the 8x8 page during a call, the timer resets
4. **Browser Restart**: Active call timers are lost if browser is closed

## Future Enhancements

Potential features for future versions:
- Multiple 8x8 instances support
- Direct Teams integration (auto-post)
- Call history log
- Custom timer thresholds
- Export call data to CSV

## Support

If you encounter issues:

1. Check the Troubleshooting section above
2. Review browser console logs (F12 → Console)
3. Verify your settings are correct
4. Try disabling and re-enabling the extension
5. Reinstall the extension as a last resort

## Version History

### v1.0.0 (Initial Release)
- Automatic call detection from 8x8 VCC
- 22-minute timer with notifications
- Auto-population of template fields
- Settings configuration page
- Copy-to-clipboard functionality
- Test mode for development

---

**Built for engineers** | No external dependencies | Privacy-focused | Open source
