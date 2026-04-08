// Background Service Worker for Long Call Update Extension
// Implements HYBRID approach: Current code + Strict rules from specification

console.log('[Long Call Update] Background service worker started');

// Store active calls (keeping Map structure but with strict rules)
let activeCalls = new Map();

// Store settings cache
let settingsCache = null;

// Timer constants
const NOTIFICATION_TIME_MS = 22 * 60 * 1000; // 22 minutes in milliseconds
const TEST_MODE_TIME_MS = 1 * 60 * 1000; // 1 minute for testing

// STRICT RULES FROM SPECIFICATION:
// 1. Timers NEVER decide if a call is active or ended
// 2. Transaction ID defines a call
// 3. Templates are tied to active calls
// 4. Calls only deleted by: user dismiss OR manual cleanup (never auto-delete during tracking!)

// Initialize on startup
async function initialize() {
  console.log('[Long Call Update] 🚀 Initializing extension v17.0.0 TRUST-BASED...');

  try {
    // Clear the active calls map FIRST
    activeCalls.clear();

    // Set badge to RED immediately (no calls)
    chrome.action.setBadgeBackgroundColor({ color: '#D71921' }); // Red
    chrome.action.setBadgeText({ text: ' ' }); // Red dot
    chrome.action.setTitle({ title: 'Long Call Update Assistant - No active calls' });

    console.log('[Long Call Update] ✅ Badge set to RED');

    // Load settings
    await loadSettings();

    // Clear ALL alarms (in case there are stale ones)
    const allAlarms = await chrome.alarms.getAll();
    console.log('[Long Call Update] Found', allAlarms.length, 'existing alarms');

    if (allAlarms.length > 0) {
      for (const alarm of allAlarms) {
        if (alarm.name.startsWith('call_timer_')) {
          console.log('[Long Call Update] Clearing stale alarm:', alarm.name);
          await chrome.alarms.clear(alarm.name);
        }
      }
    }

    console.log('[Long Call Update] ✅ Initialization complete - Ready to monitor calls');

  } catch (error) {
    console.error('[Long Call Update] Error during initialization:', error);
    // Still set badge to RED even if there's an error
    chrome.action.setBadgeBackgroundColor({ color: '#D71921' });
    chrome.action.setBadgeText({ text: ' ' });
  }
}

initialize();

// Listen for messages from content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[Long Call Update] Received message:', message.type);

  switch (message.type) {
    case 'CALL_STARTED':
      // Handle both content script and popup messages
      const tab = sender.tab || (message.data.manual ? { id: message.data.tabId || 'manual' } : null);
      console.log('[Long Call Update] 📥 CALL_STARTED message received');
      console.log('[Long Call Update]   From frame:', sender.frameId === 0 ? 'MAIN' : `IFRAME (frameId: ${sender.frameId})`);
      console.log('[Long Call Update]   Tab ID:', tab?.id);
      console.log('[Long Call Update]   URL:', sender.url);
      handleCallStarted(message.data, tab);
      sendResponse({ success: true });
      break;

    case 'CALL_ENDED':
      // DISABLED: Don't trust content script's call end detection!
      // Detection is too unreliable (flickering) and causes calls to be deleted prematurely
      // Calls will only be removed by:
      //   1. User clicking X button (DISMISS_CALL)
      //   2. Automatic cleanup after 2+ hours
      console.log('[Long Call Update] ⚠️ CALL_ENDED message received but IGNORING IT!');
      console.log('[Long Call Update] ℹ️ Content script detection is unreliable (flickering)');
      console.log('[Long Call Update] ℹ️ Call will only be removed by user dismiss or timeout');
      sendResponse({ success: true, ignored: true });
      break;

    case 'CALL_UPDATED':
      handleCallUpdated(message.data, sender.tab);
      sendResponse({ success: true });
      break;

    case 'CALL_HEARTBEAT':
      handleCallHeartbeat(message.data, sender.tab);
      sendResponse({ success: true });
      break;

    case 'GET_CURRENT_CALL':
      const currentCall = getCurrentCall();
      sendResponse({ callData: currentCall });
      break;

    case 'DISMISS_CALL':
      dismissCurrentCall();
      sendResponse({ success: true });
      break;

    case 'CREATE_MANUAL_TEMPLATE':
      // Create a manual template that persists across popup opens/closes
      const manualCallId = 'manual_' + Date.now();
      const manualCall = {
        id: manualCallId,
        tabId: sender.tab?.id || 'manual',
        transactionId: null, // Manual input required
        startTime: Date.now(),
        notified: true, // Already "notified" so template shows immediately
        dismissed: false,
        manual: true // Mark as manual
      };

      activeCalls.set(manualCallId, manualCall);
      console.log('[Long Call Update] ✅ Manual template created:', manualCall);

      // Update badge to show manual template active
      updateBadge(activeCalls.size);

      // Persist to storage
      persistCallsToStorage();

      sendResponse({ success: true, callId: manualCallId });
      break;

    case 'SETTINGS_UPDATED':
      loadSettings();
      // Notify all content scripts that settings are now configured
      chrome.tabs.query({ url: 'https://vcc-na13.8x8.com/*' }, (tabs) => {
        tabs.forEach(tab => {
          chrome.tabs.sendMessage(tab.id, { type: 'SETTINGS_CONFIGURED' }).catch(() => {
            // Content script may not be loaded yet, ignore error
          });
        });
      });
      sendResponse({ success: true });
      break;

    case 'TEMPLATE_COPIED':
      logAnalytics('template_copied');
      sendResponse({ success: true });
      break;

    case 'GET_DEBUG_INFO':
      getDebugInfo().then(debugInfo => sendResponse(debugInfo));
      break;

    case 'TRIGGER_TEST_NOTIFICATION':
      triggerTestNotification();
      sendResponse({ success: true });
      break;

    case 'CLEAR_ALL_CALLS':
      clearAllCalls();
      sendResponse({ success: true });
      break;

    default:
      sendResponse({ error: 'Unknown message type' });
  }

  return true; // Keep channel open for async response
});

// Listen for alarm events (timer notifications)
chrome.alarms.onAlarm.addListener((alarm) => {
  console.log('[Long Call Update] 🔔 Alarm triggered:', alarm.name, 'at', new Date().toLocaleTimeString());
  console.log('[Long Call Update] Alarm details:', alarm);

  if (alarm.name.startsWith('call_timer_')) {
    const callId = alarm.name.replace('call_timer_', '');
    console.log('[Long Call Update] Processing call timer for call ID:', callId);
    handleTimerExpired(callId);
  } else {
    console.log('[Long Call Update] Unknown alarm type:', alarm.name);
  }
});

// Handle call started event
async function handleCallStarted(data, tab) {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('[Long Call Update] 📞📞📞 CALL_STARTED MESSAGE RECEIVED! 📞📞📞');
  console.log('[Long Call Update] Time:', new Date().toLocaleTimeString());
  console.log('[Long Call Update] Data:', JSON.stringify(data, null, 2));
  console.log('[Long Call Update] Tab:', tab?.id);
  console.log('═══════════════════════════════════════════════════════════');

  // CRITICAL CHECK: Verify settings are configured before allowing call tracking
  const settings = await getSettings();
  console.log('[Long Call Update] Settings check:', settings);

  if (!settings.siebelId || !settings.team) {
    console.log('[Long Call Update] ❌❌❌ Settings not configured - rejecting call start');
    console.log('[Long Call Update] Please configure SIEBEL ID and TEAM in settings first');
    return;
  }

  console.log('[Long Call Update] ✅ Settings OK - proceeding...');

  const tabId = tab?.id || 'manual_' + Date.now();

  // CRITICAL: Clear any stale calls for this tab first
  console.log('[Long Call Update] 🧹 Checking for stale calls on tab:', tabId);
  let clearedStale = false;
  for (const [callId, call] of activeCalls.entries()) {
    if (call.tabId === tabId) {
      const age = Date.now() - call.startTime;
      const ageMinutes = Math.floor(age / 60000);
      console.log(`[Long Call Update]   Found existing call: ${callId} (age: ${ageMinutes}m, notified: ${call.notified}, dismissed: ${call.dismissed})`);

      // Clear stale calls (older than 5 minutes and not notified, or dismissed)
      if ((age > 300000 && !call.notified) || call.dismissed) {
        console.log(`[Long Call Update]   🗑️ Clearing stale call: ${callId}`);
        chrome.alarms.clear(`call_timer_${callId}`);
        activeCalls.delete(callId);
        clearedStale = true;
      } else {
        console.log('[Long Call Update] ⚠️ Active call already exists for this tab - updating instead');
        // Update existing call instead of creating duplicate
        call.transactionId = data.transactionId || call.transactionId;
        call.startTime = data.startTime || call.startTime;
        call.lastSeenTime = Date.now();
        activeCalls.set(callId, call);
        console.log('[Long Call Update] ✅ Updated existing call');
        await persistCallsToStorage();
        updateBadge(activeCalls.size);
        return;
      }
    }
  }

  if (clearedStale) {
    await persistCallsToStorage();
    console.log('[Long Call Update] ✅ Stale calls cleared');
  }

  const callId = generateCallId(tabId);
  console.log('[Long Call Update] 📝 Creating NEW call with ID:', callId);

  const callData = {
    id: callId,
    tabId: tabId,
    transactionId: data.transactionId,
    startTime: data.startTime || Date.now(),
    lastSeenTime: Date.now(), // NEW: Track when call was last seen active
    callDuration: 0, // NEW: Duration in seconds (updated by heartbeat)
    notified: false,
    dismissed: false,
    manual: data.manual || false
  };

  console.log('[Long Call Update] 💾 Storing call in activeCalls map...');
  console.log('[Long Call Update]   Before: activeCalls.size =', activeCalls.size);

  // Store call data IN MEMORY
  activeCalls.set(callId, callData);

  // CRITICAL VALIDATION: Verify call was actually stored
  const storedCall = activeCalls.get(callId);
  if (!storedCall) {
    console.error('[Long Call Update] ❌❌❌ CRITICAL ERROR: Call was NOT stored in map!');
    console.error('[Long Call Update] activeCalls.size:', activeCalls.size);
    console.error('[Long Call Update] Attempted to store:', callData);
    return;
  }

  console.log('[Long Call Update] ✅ Call successfully stored in map');
  console.log('[Long Call Update]   After: activeCalls.size =', activeCalls.size);
  console.log('[Long Call Update]   Stored call:', JSON.stringify(storedCall, null, 2));

  // CRITICAL: Also persist to chrome.storage.local (survives service worker restart!)
  await persistCallsToStorage();

  // Determine timer duration based on test mode
  const timerDuration = settings.testMode ? TEST_MODE_TIME_MS : NOTIFICATION_TIME_MS;

  // Create alarm for 22-minute notification (or 1 minute in test mode)
  const alarmTime = Date.now() + timerDuration;
  chrome.alarms.create(`call_timer_${callId}`, {
    when: alarmTime
  });

  const minutes = Math.floor(timerDuration / 60000);
  const seconds = Math.floor((timerDuration % 60000) / 1000);
  console.log(`[Long Call Update] ⏰ Timer set for ${minutes}m ${seconds}s (${timerDuration}ms)`);
  console.log(`[Long Call Update] Alarm will fire at: ${new Date(alarmTime).toLocaleTimeString()}`);
  console.log(`[Long Call Update] Test mode: ${settings.testMode}`);
  console.log(`[Long Call Update] Call ID: ${callId}`);

  // FINAL VALIDATION: Ensure call is still in map
  const finalCheck = activeCalls.get(callId);
  if (!finalCheck) {
    console.error('[Long Call Update] ❌❌❌ CRITICAL: Call disappeared from map after timer creation!');
    console.error('[Long Call Update] This should NEVER happen!');
  } else {
    console.log(`[Long Call Update] ✅ Final check: Call still in map`);
  }

  console.log(`[Long Call Update] 📊 Active calls count: ${activeCalls.size}`);
  console.log(`[Long Call Update] 📋 All active calls:`, Array.from(activeCalls.keys()));

  // Update badge to show active call
  console.log('[Long Call Update] 🔴 Updating badge...');
  updateBadge(activeCalls.size);

  // Double-check badge was updated
  if (activeCalls.size > 0) {
    console.log('[Long Call Update] ✅ Badge should be GREEN (active call detected)');
  } else {
    console.error('[Long Call Update] ❌ WARNING: Active calls count is 0 but call was created!');
  }

  // Verify alarm was created
  chrome.alarms.get(`call_timer_${callId}`, (alarm) => {
    if (alarm) {
      console.log('[Long Call Update] ✅✅✅ Alarm created successfully!');
      console.log('[Long Call Update] Alarm:', JSON.stringify(alarm, null, 2));
      console.log(`[Long Call Update] Will fire in ${Math.ceil((alarm.scheduledTime - Date.now()) / 1000)} seconds`);
    } else {
      console.error('[Long Call Update] ❌❌❌ CRITICAL: Failed to create alarm!');
    }
  });

  console.log('═══════════════════════════════════════════════════════════');
  console.log('[Long Call Update] ✅ handleCallStarted() complete!');
  console.log('[Long Call Update] State: Call tracked, timer running, waiting...');
  console.log('═══════════════════════════════════════════════════════════');
}

// Handle call ended event
function handleCallEnded(data, tab) {
  console.log('[Long Call Update] Call ended:', data);

  if (!tab || !tab.id) {
    console.log('[Long Call Update] No tab info, clearing all calls');
    // Clear all calls if we don't have tab info
    activeCalls.forEach((call, callId) => {
      chrome.alarms.clear(`call_timer_${callId}`);
    });
    activeCalls.clear();
    updateBadge(0);
    return;
  }

  // CRITICAL PROTECTION: NEVER delete calls during timer or after notification!
  let removedCount = 0;
  activeCalls.forEach((activeCall, callId) => {
    if (activeCall.tabId === tab.id) {
      const now = Date.now();
      const callAge = now - activeCall.startTime;

      // PROTECTION 1: Template is showing - NEVER delete!
      if (activeCall.notified) {
        console.log('[Long Call Update] ⚠️ Template is showing - IGNORING call end!');
        console.log('[Long Call Update] Call will only be removed when user clicks X');
        // Don't even clear the alarm - keep everything
        return;
      }

      // PROTECTION 2: Call is less than 2 minutes old - NEVER delete!
      // This protects against flickering detection during the critical timer period
      if (callAge < 120000) { // Less than 2 minutes = definitely still being tracked
        const ageSeconds = Math.floor(callAge / 1000);
        console.log('[Long Call Update] ⚠️ Call is only ' + ageSeconds + ' seconds old - IGNORING call end!');
        console.log('[Long Call Update] Detection flickering? Keeping call safe!');
        return;
      }

      // Only delete if timer expired AND not notified (this shouldn't happen but just in case)
      console.log('[Long Call Update] Removing call (timer expired, not notified):', callId);
      chrome.alarms.clear(`call_timer_${callId}`);
      activeCalls.delete(callId);
      removedCount++;
    }
  });

  console.log(`[Long Call Update] Removed ${removedCount} call(s) for tab ${tab.id}`);

  // Update badge - but count ALL calls (including ones with templates)
  updateBadge(activeCalls.size);
}

// Handle call updated event (e.g., transaction ID changed)
function handleCallUpdated(data, tab) {
  // Find the existing call for this tab instead of generating a new ID
  let existingCall = null;
  let existingCallId = null;

  for (const [callId, call] of activeCalls.entries()) {
    if (call.tabId === tab.id && !call.dismissed) {
      existingCall = call;
      existingCallId = callId;
      break;
    }
  }

  if (existingCall && existingCallId) {
    existingCall.transactionId = data.transactionId;
    activeCalls.set(existingCallId, existingCall);
    console.log('[Long Call Update] ✅ Transaction ID updated to:', data.transactionId);
    console.log('[Long Call Update] Updated call:', existingCall);

    // CRITICAL: Persist to storage immediately!
    persistCallsToStorage();
  } else {
    console.log('[Long Call Update] ⚠️ No active call found for tab', tab.id, '- cannot update Transaction ID');
  }
}

// Handle call heartbeat (ongoing call with duration updates)
function handleCallHeartbeat(data, tab) {
  // Find the existing call for this tab
  let existingCall = null;
  let existingCallId = null;

  for (const [callId, call] of activeCalls.entries()) {
    if (call.tabId === tab.id && !call.dismissed) {
      existingCall = call;
      existingCallId = callId;
      break;
    }
  }

  if (existingCall && existingCallId) {
    // Update call duration and last seen time
    const previousDuration = existingCall.callDuration || 0;
    existingCall.callDuration = data.duration;
    existingCall.lastSeenTime = Date.now();

    // Update Transaction ID if provided
    if (data.transactionId && data.transactionId !== existingCall.transactionId) {
      existingCall.transactionId = data.transactionId;
      console.log('[Long Call Update] ✅ Transaction ID updated via heartbeat:', data.transactionId);
    }

    activeCalls.set(existingCallId, existingCall);

    // Only log every 30 seconds to avoid spam
    if (data.duration % 30 === 0 && data.duration !== previousDuration) {
      console.log(`[Long Call Update] 💓 Heartbeat: Call active for ${Math.floor(data.duration/60)}m ${data.duration%60}s, TID: ${existingCall.transactionId || 'Not detected'}`);
    }
  }
}

// Handle timer expiration (22 minutes reached)
async function handleTimerExpired(callId) {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('[Long Call Update] ⏰⏰⏰ TIMER EXPIRED! ⏰⏰⏰');
  console.log('[Long Call Update] Call ID:', callId);
  console.log('[Long Call Update] Time:', new Date().toLocaleTimeString());
  console.log('═══════════════════════════════════════════════════════════');

  const call = activeCalls.get(callId);
  console.log('[Long Call Update] Looking up call in map...');
  console.log('[Long Call Update] Call found:', call ? 'YES ✅' : 'NO ❌');
  console.log('[Long Call Update] Call data:', JSON.stringify(call, null, 2));
  console.log('[Long Call Update] All active calls:', activeCalls.size);
  console.log('[Long Call Update] Active calls map:', JSON.stringify(Array.from(activeCalls.entries()), null, 2));

  if (!call) {
    console.error('[Long Call Update] ❌❌❌ CRITICAL ERROR: Call not found in activeCalls map!');
    console.error('[Long Call Update] This means the call was deleted before timer expired!');
    console.error('[Long Call Update] Check for CALL_ENDED messages or deletion logs above!');
    return;
  }

  if (call.notified) {
    console.log('[Long Call Update] Call already notified, skipping');
    return;
  }

  // ═══════════════════════════════════════════════════════════════
  // USE HEARTBEAT DATA: Heartbeats come from control_frame and are reliable!
  // ═══════════════════════════════════════════════════════════════

  console.log('[Long Call Update] 📊 CHECKING HEARTBEAT DATA (from control_frame):');

  const now = Date.now();
  const timeSinceLastSeen = now - (call.lastSeenTime || call.startTime);
  const hasTransactionId = call.transactionId &&
                          call.transactionId !== 'Not found' &&
                          call.transactionId !== 'Not detected';
  const hasCallDuration = call.callDuration && call.callDuration > 0;
  const hasRecentHeartbeat = timeSinceLastSeen < 15000; // Within 15 seconds

  console.log('[Long Call Update]   Transaction ID (from heartbeat):', call.transactionId || '❌ None');
  console.log('[Long Call Update]   Call Duration (from heartbeat):', hasCallDuration ? `${Math.floor(call.callDuration/60)}m ${call.callDuration%60}s` : '❌ None');
  console.log('[Long Call Update]   Last Heartbeat:', `${Math.floor(timeSinceLastSeen/1000)}s ago`);
  console.log('[Long Call Update]   Recent Heartbeat (<15s):', hasRecentHeartbeat ? '✅ YES' : '❌ NO');

  // ═══════════════════════════════════════════════════════════════
  // AUTO-RESET LOGIC: Based on heartbeat data from control_frame
  // ═══════════════════════════════════════════════════════════════

  // AUTO-RESET if NO recent heartbeat (means call ended in control_frame)
  if (!hasRecentHeartbeat) {
    console.log('[Long Call Update] ⚠️⚠️⚠️ NO RECENT HEARTBEAT - CALL ENDED - AUTO-RESETTING!');
    console.log('[Long Call Update] ℹ️ No heartbeat from control_frame for >15 seconds');
    console.log('[Long Call Update] ℹ️ This means call duration disappeared from control_frame');

    // Clear this call
    chrome.alarms.clear(`call_timer_${callId}`);
    activeCalls.delete(callId);
    await persistCallsToStorage();
    updateBadge(activeCalls.size);

    console.log('[Long Call Update] ✅ Auto-reset complete - ready for next call');
    console.log('═══════════════════════════════════════════════════════════');
    return;
  }

  // If we have recent heartbeat, call is active!
  console.log('[Long Call Update] ✅ RECENT HEARTBEAT CONFIRMS CALL IS ACTIVE');
  console.log('[Long Call Update]   Transaction ID:', call.transactionId || 'Not detected');
  console.log('[Long Call Update]   Duration:', call.callDuration ? `${Math.floor(call.callDuration/60)}m ${call.callDuration%60}s` : 'N/A');
  console.log('[Long Call Update] ✅ Proceeding with template');

  // Mark as notified
  console.log('[Long Call Update] Marking call as notified...');
  call.notified = true;
  call.notifiedTime = Date.now();
  activeCalls.set(callId, call);

  // CRITICAL: Persist to storage immediately!
  await persistCallsToStorage();

  console.log('[Long Call Update] ✅✅✅ Call marked as notified! Template should appear now!');
  console.log('[Long Call Update] Updated call:', JSON.stringify(call, null, 2));

  // Show notification
  console.log('[Long Call Update] Showing browser notification...');
  await showNotification(call);

  // CRITICAL: Badge stays GREEN! (Call is still active per spec!)
  // "Badge MUST remain green while callState ≠ ENDED"
  // Timer expiring does NOT mean call ended!
  chrome.action.setBadgeBackgroundColor({ color: '#28a745' }); // Keep GREEN!
  chrome.action.setBadgeText({ text: '●' });
  chrome.action.setTitle({ title: 'Template ready - Call still active' });
  console.log('[Long Call Update] ✅ Badge STAYS GREEN (call still active per spec!)');
  console.log('[Long Call Update] ℹ️ Timer expired ≠ Call ended');
  console.log('[Long Call Update] ✅✅✅ TEMPLATE READY - User can open popup now!');
  console.log('═══════════════════════════════════════════════════════════');
}

// Show browser notification
async function showNotification(call) {
  const settings = await getSettings();

  const notificationOptions = {
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: 'Long Call Update - Copy Template Now',
    message: `Call has reached ${settings.testMode ? '1' : '22'} minutes. Copy and paste the template now. Transaction ID: ${call.transactionId || 'Not detected'}`,
    priority: 2,
    requireInteraction: true,
    buttons: [
      { title: 'Copy Template' }
    ]
  };

  chrome.notifications.create(`call_notification_${call.id}`, notificationOptions);
}

// Handle notification button clicks
chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
  if (notificationId.startsWith('call_notification_')) {
    if (buttonIndex === 0) {
      // Open popup
      chrome.action.openPopup();
    }
    chrome.notifications.clear(notificationId);
  }
});

// Handle notification clicks
chrome.notifications.onClicked.addListener((notificationId) => {
  if (notificationId.startsWith('call_notification_')) {
    chrome.action.openPopup();
    chrome.notifications.clear(notificationId);
  }
});

// Get current call (for popup)
function getCurrentCall() {
  // Return ONLY notified calls (calls that reached 22 min / 1 min)
  // Don't return calls that are just being tracked but haven't reached the time yet
  for (const [id, call] of activeCalls.entries()) {
    if (call.notified && !call.dismissed) {
      return call;
    }
  }

  // Return null if no notified call exists (means call is still being tracked, timer not expired yet)
  return null;
}

// Dismiss current call
async function dismissCurrentCall() {
  console.log('[Long Call Update] 🔍 X BUTTON CLICKED - Checking heartbeat data...');

  const currentCall = getCurrentCall();
  if (!currentCall) {
    console.log('[Long Call Update] No current call found, clearing all active calls');
    await clearAllCalls();
    updateBadge(activeCalls.size);
    return;
  }

  // ═══════════════════════════════════════════════════════════════
  // SPECIAL CASE: Manual templates (no heartbeat expected)
  // ═══════════════════════════════════════════════════════════════

  if (currentCall.manual) {
    console.log('[Long Call Update] 📝 MANUAL TEMPLATE - User cancelled');
    console.log('[Long Call Update] ℹ️ Removing manual template from tracking');

    // Remove manual template completely
    activeCalls.delete(currentCall.id);
    await persistCallsToStorage();

    console.log('[Long Call Update] ✅ Manual template removed');
    console.log('[Long Call Update] Active calls remaining:', activeCalls.size);

    updateBadge(activeCalls.size);
    console.log('[Long Call Update] ✓ Dismiss operation complete');
    return;
  }

  // ═══════════════════════════════════════════════════════════════
  // USE HEARTBEAT DATA: Heartbeats come from control_frame
  // ═══════════════════════════════════════════════════════════════

  const now = Date.now();
  const timeSinceLastSeen = now - (currentCall.lastSeenTime || currentCall.startTime);
  const hasRecentHeartbeat = timeSinceLastSeen < 15000; // Within 15 seconds

  console.log('[Long Call Update] 📊 HEARTBEAT DATA CHECK:');
  console.log('[Long Call Update]   Transaction ID (from heartbeat):', currentCall.transactionId || '❌ None');
  console.log('[Long Call Update]   Call Duration (from heartbeat):', currentCall.callDuration ? `${Math.floor(currentCall.callDuration/60)}m ${currentCall.callDuration%60}s` : '❌ None');
  console.log('[Long Call Update]   Last Heartbeat:', `${Math.floor(timeSinceLastSeen/1000)}s ago`);
  console.log('[Long Call Update]   Recent Heartbeat (<15s):', hasRecentHeartbeat ? '✅ YES' : '❌ NO');

  // ═══════════════════════════════════════════════════════════════
  // DECISION: Based on heartbeat (from control_frame)
  // ═══════════════════════════════════════════════════════════════

  if (hasRecentHeartbeat) {
    console.log('[Long Call Update] ⚠️ CALL IS STILL ACTIVE (recent heartbeat from control_frame)');
    console.log('[Long Call Update] ℹ️ Action: Dismissing template but keeping call tracked');

    // Only dismiss the notification state, keep call tracked
    currentCall.notified = false;
    currentCall.dismissed = false;
    activeCalls.set(currentCall.id, currentCall);
    await persistCallsToStorage();

    console.log('[Long Call Update] ✅ Template dismissed, call still tracked');
  } else {
    console.log('[Long Call Update] ✅ CALL HAS ENDED (no recent heartbeat)');
    console.log('[Long Call Update] ℹ️ No heartbeat for >15s = call duration gone from control_frame');
    console.log('[Long Call Update] ℹ️ Proceeding with full dismissal');

    // Clear the alarm
    chrome.alarms.clear(`call_timer_${currentCall.id}`);

    // Remove from active calls completely
    activeCalls.delete(currentCall.id);

    // CRITICAL: Persist deletion to storage!
    await persistCallsToStorage();

    console.log('[Long Call Update] ✅ Call dismissed and removed');
    console.log('[Long Call Update] Active calls remaining:', activeCalls.size);
  }

  // Reset badge
  updateBadge(activeCalls.size);

  console.log('[Long Call Update] ✓ Dismiss operation complete');
}

// Clear all active calls and alarms
async function clearAllCalls() {
  console.log('[Long Call Update] 🗑️ Clearing ALL active calls');

  // Clear all alarms
  for (const [callId] of activeCalls.entries()) {
    chrome.alarms.clear(`call_timer_${callId}`);
    console.log('[Long Call Update]   Cleared alarm for:', callId);
  }

  // Clear the map
  activeCalls.clear();

  // CRITICAL: Persist cleared state to storage!
  await persistCallsToStorage();

  // Reset badge to RED
  updateBadge(0);

  console.log('[Long Call Update] ✅ All calls cleared - badge reset to RED');
}

// Update extension badge
function updateBadge(count) {
  console.log('[Long Call Update] 🎨 UPDATING BADGE - Active calls count:', count);

  if (count === 0) {
    // RED badge when NO calls
    console.log('[Long Call Update]   Setting badge to RED (no active calls)');
    chrome.action.setBadgeBackgroundColor({ color: '#D71921' }); // Trend Micro Red
    chrome.action.setBadgeText({ text: ' ' }); // Red dot
    chrome.action.setTitle({ title: 'Long Call Update Assistant - No active calls' });
  } else {
    // GREEN badge when call is active
    console.log('[Long Call Update]   Setting badge to GREEN (', count, 'active call' + (count > 1 ? 's)' : ')'));
    chrome.action.setBadgeBackgroundColor({ color: '#28a745' }); // Green
    chrome.action.setBadgeText({ text: ' ' }); // Green dot
    chrome.action.setTitle({ title: `Call active - Timer running (${count} call${count > 1 ? 's' : ''})` });
  }
}

// Generate unique call ID
function generateCallId(tabId) {
  return `tab_${tabId}_${Date.now()}`;
}

// Load and cache settings
async function loadSettings() {
  try {
    settingsCache = await chrome.storage.sync.get({
      siebelId: '',
      team: '',
      skillset: 'PS',
      testMode: false
    });
    console.log('[Long Call Update] Settings loaded:', settingsCache);
  } catch (error) {
    console.error('[Long Call Update] Error loading settings:', error);
    settingsCache = {
      siebelId: '',
      team: '',
      skillset: 'PS',
      testMode: false
    };
  }
}

// Get settings (from cache or load)
async function getSettings() {
  if (!settingsCache) {
    await loadSettings();
  }
  return settingsCache;
}

// Log analytics (simple counter for now)
function logAnalytics(event) {
  chrome.storage.local.get({ analytics: {} }, (result) => {
    const analytics = result.analytics;
    analytics[event] = (analytics[event] || 0) + 1;
    analytics.last_event = new Date().toISOString();

    chrome.storage.local.set({ analytics });
    console.log('[Long Call Update] Analytics:', event, analytics[event]);
  });
}

// Get debug information
async function getDebugInfo() {
  const settings = await getSettings();
  const activeCallsArray = Array.from(activeCalls.values());

  return {
    activeCalls: activeCallsArray,
    activeCallsCount: activeCalls.size,
    settings: settings,
    testMode: settings.testMode,
    timerDuration: settings.testMode ? '1 minute' : '22 minutes'
  };
}

// Trigger test notification immediately
async function triggerTestNotification() {
  console.log('[Long Call Update] Triggering test notification');

  // Get the most recent call or create a test one
  let testCall = getCurrentCall();

  if (!testCall) {
    // Create a test call
    const testCallId = 'test_' + Date.now();
    testCall = {
      id: testCallId,
      tabId: 'test',
      transactionId: null,
      startTime: Date.now() - (22 * 60 * 1000),
      notified: false,
      dismissed: false,
      test: true
    };
    activeCalls.set(testCallId, testCall);
  }

  // Mark as notified and show notification
  testCall.notified = true;
  activeCalls.set(testCall.id, testCall);

  await showNotification(testCall);

  // Set badge to alert state
  chrome.action.setBadgeBackgroundColor({ color: '#FF0000' });
  chrome.action.setBadgeText({ text: '!' });

  console.log('[Long Call Update] Test notification shown');
}

// Cleanup old calls periodically
setInterval(() => {
  const now = Date.now();
  const maxAge = 4 * 60 * 60 * 1000; // 4 hours

  for (const [id, call] of activeCalls.entries()) {
    if (now - call.startTime > maxAge) {
      console.log('[Long Call Update] Cleaning up old call:', id);
      chrome.alarms.clear(`call_timer_${id}`);
      activeCalls.delete(id);
    }
  }

  updateBadge(activeCalls.size);
}, 30 * 60 * 1000); // Run every 30 minutes

// ═══════════════════════════════════════════════════════════════
// PERSISTENCE: Survive service worker restarts!
// ═══════════════════════════════════════════════════════════════

// Save active calls to chrome.storage.local
async function persistCallsToStorage() {
  try {
    const callsArray = Array.from(activeCalls.entries());
    await chrome.storage.local.set({
      activeCalls: callsArray,
      lastPersisted: Date.now()
    });
    console.log('[Long Call Update] 💾 Persisted', activeCalls.size, 'calls to storage');
  } catch (error) {
    console.error('[Long Call Update] ❌ Failed to persist calls:', error);
  }
}

// Restore active calls from chrome.storage.local
async function restoreCallsFromStorage() {
  try {
    const data = await chrome.storage.local.get(['activeCalls', 'lastPersisted']);

    if (data.activeCalls && Array.isArray(data.activeCalls)) {
      activeCalls = new Map(data.activeCalls);
      console.log('[Long Call Update] ✅ Restored', activeCalls.size, 'calls from storage');
      console.log('[Long Call Update] Last persisted:', new Date(data.lastPersisted).toLocaleString());

      // Recreate alarms for restored calls
      for (const [callId, call] of activeCalls.entries()) {
        if (!call.notified) {
          const settings = await getSettings();
          const timerDuration = settings.testMode ? TEST_MODE_TIME_MS : NOTIFICATION_TIME_MS;
          const elapsed = Date.now() - call.startTime;
          const remaining = timerDuration - elapsed;

          if (remaining > 0) {
            // Call still has time left - recreate alarm
            const alarmTime = Date.now() + remaining;
            await chrome.alarms.create(`call_timer_${callId}`, { when: alarmTime });
            console.log('[Long Call Update] ⏰ Recreated alarm for call', callId, 'fires in', Math.floor(remaining/1000), 's');
          } else {
            // Timer already expired - mark as notified immediately
            call.notified = true;
            call.notifiedTime = Date.now();
            activeCalls.set(callId, call);
            console.log('[Long Call Update] ⚠️ Call timer already expired - marking as notified');
          }
        }
      }

      // Update badge based on restored calls
      updateBadge(activeCalls.size);

      return true;
    } else {
      console.log('[Long Call Update] No calls to restore from storage');
      return false;
    }
  } catch (error) {
    console.error('[Long Call Update] ❌ Failed to restore calls:', error);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════
// EXTENSION RELOAD HANDLER
// ═══════════════════════════════════════════════════════════════

chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('[Long Call Update] Extension installed/updated:', details.reason);

  // Try to restore calls from storage first!
  const restored = await restoreCallsFromStorage();

  if (restored) {
    console.log('[Long Call Update] ✅ State restored! Calls survived service worker restart!');
  }

  await reinitializeContentScripts();
});

// Also restore state when service worker restarts (happens every ~30 seconds!)
console.log('[Long Call Update] Service worker starting - restoring state...');
restoreCallsFromStorage().then(() => {
  reinitializeContentScripts();
});

async function reinitializeContentScripts() {
  try {
    // Find all 8x8 tabs
    const tabs = await chrome.tabs.query({ url: 'https://vcc-na13.8x8.com/*' });

    console.log('[Long Call Update] Found', tabs.length, '8x8 tabs to reinitialize');

    for (const tab of tabs) {
      try {
        // Try to ping the existing content script
        const response = await chrome.tabs.sendMessage(tab.id, { type: 'REINITIALIZE' });
        console.log('[Long Call Update] Content script reinitialized in tab', tab.id, response);
      } catch (error) {
        // Content script not loaded yet - inject it
        console.log('[Long Call Update] No content script in tab', tab.id, '- injecting...');
        try {
          await chrome.scripting.executeScript({
            target: { tabId: tab.id, allFrames: true },
            files: ['content.js']
          });
          console.log('[Long Call Update] ✅ Content script injected into tab', tab.id);
        } catch (injectError) {
          console.error('[Long Call Update] Failed to inject content script:', injectError);
        }
      }
    }

    console.log('[Long Call Update] ✅ All content scripts reinitialized - engineers do NOT need to refresh!');
  } catch (error) {
    console.error('[Long Call Update] Error reinitializing content scripts:', error);
  }
}
