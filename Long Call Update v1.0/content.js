// Content script for 8x8 VCC interface integration
// Detects active calls and extracts Transaction ID

// CRITICAL: Prevent multiple script injections
if (window.longCallUpdateContentScriptLoaded) {
  console.log('[Long Call Update] ⚠️ Content script already loaded - skipping duplicate injection');
} else {
  window.longCallUpdateContentScriptLoaded = true;

console.log('╔════════════════════════════════════════════════════════════════╗');
console.log('║  [Long Call Update] Content Script v19.1.0 DURATION-BASED     ║');
console.log('╠════════════════════════════════════════════════════════════════╣');
console.log('║  🎯 BETA APPROACH: Call duration = source of truth!           ║');
console.log('║  ✅ Duration timer exists → Call is active                     ║');
console.log('║  ✅ Duration increases → Call ongoing                          ║');
console.log('║  ✅ Duration disappears 15s → Call ended + auto-reset         ║');
console.log('║  ✅ Duration resets → New call started                         ║');
console.log('║  🛡️ Clean error handling (no spam on reload!)                 ║');
console.log('║  🎉 RESULT: Reliable + auto-reset + no manual reload needed!  ║');
console.log('╠════════════════════════════════════════════════════════════════╣');
console.log('║  URL:', window.location.href);
console.log('║  Frame Type:', window === window.top ? 'MAIN FRAME' : 'IFRAME');
console.log('║  Frame Name:', window.name || '(unnamed)');
console.log('║  Page Title:', document.title);
console.log('║  Body exists:', !!document.body);
console.log('║  Elements on page:', document.body ? document.querySelectorAll('*').length : 0);
console.log('╚════════════════════════════════════════════════════════════════╝');

// Configuration for DOM selectors (can be customized if needed)
const CONFIG = {
  // Common selectors to try for transaction ID
  transactionIdSelectors: [
    '[data-test="transaction-id"]',
    '[aria-label*="Transaction"]',
    '[aria-label*="transaction"]',
    '[aria-label*="Interaction"]',
    '[aria-label*="interaction"]',
    '[class*="transaction"]',
    '[class*="Transaction"]',
    '[class*="interaction"]',
    '[class*="Interaction"]',
    '[id*="transaction"]',
    '[id*="interaction"]',
    '.transaction-id',
    '#transactionId',
    '[name="transactionId"]',
    '[data-interaction-id]',
    '[data-transaction-id]'
  ],

  // Selectors for detecting active call state
  callActiveSelectors: [
    '[data-test="call-active"]',
    '[aria-label*="Call in progress"]',
    '.call-active',
    '.call-status.active',
    '[data-call-state="active"]',
    '.agent-status.on-call'
  ],

  // How often to check for changes (in ms)
  pollingInterval: 3000, // Check every 3 seconds (prevent duplicates)

  // Debounce time for MutationObserver (in ms)
  debounceTime: 500 // Prevent excessive checks
};

let currentCallState = {
  isActive: false,
  transactionId: null,
  lastCheck: null,
  lastDetectionTime: null, // Track when we last detected a call
  consecutiveMisses: 0, // Count how many times in a row we DON'T detect the call
  lastCallDuration: 0, // NEW: Track last seen call duration in seconds
  callDurationDecreased: false // NEW: Flag if duration decreased (means new call!)
};

let observer = null;
let debounceTimer = null;
let pollingTimer = null;

// Cooldown to prevent duplicate detections (in ms)
const DETECTION_COOLDOWN = 10000; // 10 seconds

// Initialize the content script
function initialize() {
  console.log('[Long Call Update] Initializing 8x8 integration...');
  console.log('[Long Call Update] Waiting for page to fully load...');

  // Start observing DOM changes (but checks will be blocked until settings exist)
  startDOMObserver();

  // Also use polling as a fallback
  startPolling();

  // Delay initial check by 5 seconds to avoid false detections on page load
  setTimeout(() => {
    console.log('[Long Call Update] Running initial call status check...');
    checkCallStatus();
  }, 5000);
}

// Start watching for DOM changes using MutationObserver
function startDOMObserver() {
  // Don't start if already running
  if (observer) {
    console.log('[Long Call Update] Observer already running - skipping');
    return;
  }

  observer = new MutationObserver(() => {
    // Always observe, but debounce to avoid excessive checks
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      checkCallStatus();
    }, CONFIG.debounceTime);
  });

  // Observe the entire document body for changes
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'data-call-state', 'aria-label']
  });

  console.log('[Long Call Update] ✅ DOM observer started (runs continuously, never stops!)');
}

// Start polling (always runs, never stops!)
function startPolling() {
  // Don't start if already running
  if (pollingTimer) {
    console.log('[Long Call Update] Polling already running - skipping');
    return;
  }

  pollingTimer = setInterval(() => {
    // Always check, but cooldown prevents duplicate CALL_STARTED messages
    checkCallStatus();
  }, CONFIG.pollingInterval);

  console.log('[Long Call Update] ✅ Polling started (checks every 3 seconds, never stops!)');
}

// Check if agent is on break/AUX (should NOT detect calls)
function isOnBreakOrAux() {
  // CRITICAL: Only check break status in main window (not in iframes)
  // The break status UI is in the main frame, not control_frame
  if (window !== window.top) {
    // We're in an iframe - can't check break status here
    return false;
  }

  // Method 1: Check for on-break-wrapper div (most reliable)
  const onBreakWrapper = document.getElementById('on-break-wrapper');
  if (onBreakWrapper) {
    console.log('[Long Call Update] ⚠️⚠️⚠️ AGENT ON BREAK - on-break-wrapper found');
    return true;
  }

  // Method 2: Check for "Ready to work" button with specific test ID
  const readyToWorkButton = document.querySelector('[data-test-id="on-break-page-button-ready-to-work"]');
  if (readyToWorkButton) {
    console.log('[Long Call Update] ⚠️⚠️⚠️ AGENT ON BREAK - Ready to work button found');
    return true;
  }

  // Method 3: Check for break timer
  const onBreakTimer = document.querySelector('[data-test-id="on-break-timer"]');
  if (onBreakTimer) {
    console.log('[Long Call Update] ⚠️⚠️⚠️ AGENT ON BREAK - Break timer found');
    return true;
  }

  // Method 4: Check for "On Break for:" text in h1
  const breakHeading = Array.from(document.querySelectorAll('h1')).find(h1 =>
    h1.textContent.includes('On Break for')
  );
  if (breakHeading) {
    console.log('[Long Call Update] ⚠️⚠️⚠️ AGENT ON BREAK - "On Break for:" heading found');
    return true;
  }

  return false;
}

// Main function to check if a call is active and extract data
function checkCallStatus() {
  const now = Date.now();
  currentCallState.lastCheck = now;

  // ═══════════════════════════════════════════════════════════════
  // CRITICAL: Skip detection if agent is on break/AUX
  // ═══════════════════════════════════════════════════════════════

  const onBreak = isOnBreakOrAux();

  if (onBreak) {
    console.log('[Long Call Update] ⏸️⏸️⏸️ AGENT ON BREAK - SKIPPING CALL DETECTION ⏸️⏸️⏸️');
    // If we thought there was a call, clear it
    if (currentCallState.isActive) {
      console.log('[Long Call Update] ℹ️ Clearing call state (agent went on break)');
      handleCallEnd();
    }
    return;
  } else {
    // Only log occasionally to avoid spam (every 30 seconds)
    if (now % 30000 < 3000) {
      console.log('[Long Call Update] ✅ Agent available - monitoring for calls');
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // CRITICAL: Check if we're on a page that could have active calls
  // Skip pages like "Interaction history" which show old call data
  // ═══════════════════════════════════════════════════════════════

  const pageTitle = document.title || '';
  const bodyText = document.body.innerText || '';

  // Skip if on pages that are NOT active calls
  const excludedPages = [
    'Interaction history',
    'interaction history',
    'My recordings',
    'Recorded interactions',
    'Contact Center interaction'  // Past interactions
  ];

  for (const excluded of excludedPages) {
    if (pageTitle.includes(excluded) || bodyText.includes(excluded)) {
      console.log('[Long Call Update] ⚠️ On excluded page:', excluded, '- skipping detection');
      return;
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // Extract call data from control_frame
  // ═══════════════════════════════════════════════════════════════

  const currentDuration = extractCallDuration();
  const transactionId = extractTransactionId();

  // CRITICAL RULE: Transaction ID + Call Duration are ALWAYS together!
  // Duration alone is NOT enough (could be break timer, offline timer, etc.)
  const hasTransactionId = transactionId &&
                          transactionId !== 'Not found' &&
                          transactionId !== 'Not detected';
  const hasDuration = currentDuration !== null && currentDuration >= 0;

  console.log('[Long Call Update] 📊 Check:', {
    duration: currentDuration ? `${Math.floor(currentDuration/60)}m ${currentDuration%60}s` : 'none',
    transactionId: transactionId || 'none',
    hasTransactionId: hasTransactionId ? '✅' : '❌',
    hasDuration: hasDuration ? '✅' : '❌',
    bothExist: (hasTransactionId && hasDuration) ? '✅ ACTIVE CALL' : '❌ NOT A CALL',
    isActive: currentCallState.isActive
  });

  // ═══════════════════════════════════════════════════════════════
  // ONLY detect call if BOTH duration AND Transaction ID exist
  // ═══════════════════════════════════════════════════════════════

  if (hasDuration && hasTransactionId) {
    // BOTH exist → This is an actual call!

    if (!currentCallState.isActive) {
      // NEW call just started!
      console.log('[Long Call Update] 🆕 NEW CALL detected (duration timer appeared)!');
      currentCallState.lastCallDuration = currentDuration;
      currentCallState.consecutiveMisses = 0;
      handleCallStart();

    } else {
      // Ongoing call

      // Check if duration DECREASED (means new call started!)
      if (currentCallState.lastCallDuration > 60 && currentDuration < 30) {
        console.log('[Long Call Update] 🔄 Duration RESET detected - NEW CALL!');
        console.log(`[Long Call Update]    Old: ${currentCallState.lastCallDuration}s → New: ${currentDuration}s`);

        // End old call, start new one
        handleCallEnd();
        currentCallState.lastCallDuration = currentDuration;
        handleCallStart();

      } else {
        // Same call continuing
        console.log(`[Long Call Update] ✅ Call ONGOING - ${Math.floor(currentDuration/60)}m ${currentDuration%60}s`);
        currentCallState.lastCallDuration = currentDuration;
        currentCallState.consecutiveMisses = 0; // Reset

        // NEW: Send heartbeat with call duration to background script
        // This helps verify the call is truly still active
        notifyBackgroundScript('CALL_HEARTBEAT', {
          duration: currentDuration,
          transactionId: transactionId || currentCallState.transactionId
        });

        // Update Transaction ID if it changed or appeared
        if (transactionId && transactionId !== currentCallState.transactionId) {
          console.log('[Long Call Update] Transaction ID updated:', transactionId);
          currentCallState.transactionId = transactionId;
          notifyBackgroundScript('CALL_UPDATED', { transactionId });
        }
      }
    }

  } else {
    // NO duration timer found → No call OR call ended

    if (currentCallState.isActive) {
      // Call was active but timer disappeared
      currentCallState.consecutiveMisses++;
      console.log(`[Long Call Update] ⚠️ Duration timer disappeared (miss #${currentCallState.consecutiveMisses}/5)`);

      // Only need 5 misses (15 seconds) since duration is reliable
      if (currentCallState.consecutiveMisses >= 5) {
        console.log('[Long Call Update] ✅ Call ENDED (duration timer gone for 15s)');
        currentCallState.lastCallDuration = 0;
        handleCallEnd();
      }
    } else {
      // No call active - normal state, keep monitoring
    }
  }
}

// Detect if a call is currently active
function detectActiveCall() {
  console.log('[Long Call Update] 🔍 Checking for active call...');
  console.log('[Long Call Update]  › Frame:', window === window.top ? 'Main' : window.name || 'Iframe');

  // CRITICAL: Only detect calls on the actual 8x8 page
  if (!window.location.href.includes('8x8.com')) {
    console.log('[Long Call Update] ❌ Not on 8x8 domain - skipping detection');
    return false;
  }

  // Get page text for checks
  const bodyText = document.body.innerText || '';
  const bodyTextLower = bodyText.toLowerCase();

  // CRITICAL EXCLUSION LIST: Pages that are NOT active calls
  const excludedPages = [
    'interaction history',
    'interaction details',
    'my recordings',
    'my profile',
    'transcription',
    'agent details',
    'customer details',
    'settings',
    'queues',
    'about',
    'site map',
    'knowledge base'
  ];

  for (const page of excludedPages) {
    if (bodyTextLower.includes(page)) {
      console.log('[Long Call Update] ❌ On excluded page (' + page + ') - skipping');
      return false;
    }
  }

  // Check for history navigation buttons
  if ((bodyText.includes('Previous') && bodyText.includes('Next')) ||
      (bodyText.includes('Back') && bodyText.includes('Next'))) {
    console.log('[Long Call Update] ❌ History navigation detected - skipping');
    return false;
  }

  // ═══════════════════════════════════════════════════════════════
  // UNIVERSAL DETECTION METHOD
  // ═══════════════════════════════════════════════════════════════
  // Transaction ID ONLY exists during ACTIVE calls!
  // Works for BOTH callers AND receivers!
  // ═══════════════════════════════════════════════════════════════

  // Look for Transaction ID in the page
  const allListItems = document.querySelectorAll('li');

  for (const li of allListItems) {
    const liText = li.textContent || '';

    // Check if this <li> contains "Transaction ID" label
    if (liText.includes('Transaction ID')) {
      // Found the label! Now check if there's a numeric value
      const spans = li.querySelectorAll('span');

      for (const span of spans) {
        const spanText = span.textContent.trim();
        const spanTitle = span.getAttribute('title') || '';

        // Check if this span contains a numeric Transaction ID (3-8 digits)
        const tidText = /^\d{3,8}$/.test(spanText) ? spanText : null;
        const tidTitle = /^\d{3,8}$/.test(spanTitle) ? spanTitle : null;
        const tid = tidText || tidTitle;

        if (tid) {
          console.log('[Long Call Update] ✅ ACTIVE CALL DETECTED - Transaction ID:', tid);
          return true;
        }
      }
    }
  }

  // No Transaction ID found = No active call
  console.log('[Long Call Update] ❌ No active call (no Transaction ID found)');
  return false;
}

// Extract call duration from 8x8 timer display
// Returns duration in seconds, or null if no timer found
function extractCallDuration() {
  // CRITICAL: Use the SPECIFIC interaction-timer element (NOT agent status timer!)
  // The interaction-timer shows the actual call duration
  // The user-presence-timer shows agent status duration (WRONG!)

  const interactionTimer = document.querySelector('[data-test-id="interaction-timer"]');

  if (interactionTimer) {
    const timerText = interactionTimer.textContent.trim();
    console.log('[Long Call Update] ⏱️ Found interaction-timer element:', timerText);

    // Parse the timer text (formats: "MM:SS", "H:MM:SS", "M:SS")
    const colonMatch = timerText.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/);

    if (colonMatch) {
      let totalSeconds = 0;

      if (colonMatch[3]) {
        // Format: H:MM:SS
        const hours = parseInt(colonMatch[1]);
        const minutes = parseInt(colonMatch[2]);
        const seconds = parseInt(colonMatch[3]);
        totalSeconds = (hours * 3600) + (minutes * 60) + seconds;
        console.log('[Long Call Update] ⏱️ Call duration (H:MM:SS):', `${hours}:${minutes}:${seconds}`, '=', totalSeconds, 'seconds');
      } else {
        // Format: MM:SS or M:SS
        const minutes = parseInt(colonMatch[1]);
        const seconds = parseInt(colonMatch[2]);
        totalSeconds = (minutes * 60) + seconds;
        console.log('[Long Call Update] ⏱️ Call duration (MM:SS):', `${minutes}:${seconds}`, '=', totalSeconds, 'seconds');
      }

      return totalSeconds;
    }
  }

  console.log('[Long Call Update] ⏱️ No interaction-timer element found (no active call)');
  return null;
}

// Extract Transaction ID from the page
// 8x8 Transaction IDs can be any numeric value (typically 3-8 digits)
function extractTransactionId() {
  console.log('[Long Call Update] 🔍 Extracting Transaction ID...');
  console.log('[Long Call Update]  › Frame:', window === window.top ? 'Main' : window.name || 'Iframe');

  // Get page text for fallback methods
  const allText = document.body.innerText || '';

  // Look through all <li> elements to find Transaction ID
  const allListItems = document.querySelectorAll('li');
  console.log('[Long Call Update]  › Checking', allListItems.length, 'list items...');

  for (const li of allListItems) {
    const liText = li.textContent || '';

    // Check if this <li> contains "Transaction ID" label (case insensitive!)
    if (liText.toLowerCase().includes('transaction id')) {
      console.log('[Long Call Update]  › Found <li> with "Transaction ID"!');
      console.log('[Long Call Update]  › Full <li> text:', liText);

      // Get ALL text content and ALL elements
      const spans = li.querySelectorAll('span');
      const divs = li.querySelectorAll('div');
      const allElements = [...spans, ...divs];

      console.log('[Long Call Update]  › Found', allElements.length, 'elements to check');

      // Look for ANY numeric value
      let foundValues = [];
      for (const elem of allElements) {
        const title = elem.getAttribute('title');
        const text = elem.textContent.trim();

        // Collect all numeric values (ANY length!)
        if (title && /^\d+$/.test(title)) {
          foundValues.push({ source: 'title', value: title, elem: elem.tagName });
        }
        if (text && /^\d+$/.test(text) && !text.toLowerCase().includes('transaction')) {
          foundValues.push({ source: 'text', value: text, elem: elem.tagName });
        }
      }

      console.log('[Long Call Update]  › All numeric values found:', foundValues);

      // Return the FIRST numeric value found (highest priority)
      if (foundValues.length > 0) {
        const tid = foundValues[0].value;
        console.log('[Long Call Update] ✅ Transaction ID found (from', foundValues[0].source + '):', tid);
        return tid;
      }

      // Fallback: Extract any number from the entire <li> text
      const numbers = liText.match(/\b\d+\b/g);
      if (numbers && numbers.length > 0) {
        // Filter out numbers that are part of the label itself
        const validNumbers = numbers.filter(num => {
          return num.length >= 2 && // At least 2 digits
                 num !== 'ID' &&
                 num.length <= 8; // Max 8 digits
        });

        if (validNumbers.length > 0) {
          console.log('[Long Call Update] ✅ Transaction ID extracted from text:', validNumbers[0]);
          return validNumbers[0];
        }
      }

      console.log('[Long Call Update] ⚠️ Found "Transaction ID" label but no valid numeric value');
    }
  }

  // METHOD 2: Look for numeric ID near "Transaction ID" text
  const textLines = allText.split('\n');
  for (let i = 0; i < textLines.length; i++) {
    const line = textLines[i];
    if (/Transaction\s*ID/i.test(line)) {
      // Check this line and the next 5 lines
      for (let j = i; j < Math.min(i + 6, textLines.length); j++) {
        const checkLine = textLines[j].trim();

        // Accept any numeric ID with at least 3 digits
        if (/^\d+$/.test(checkLine) && checkLine.length >= 3) {
          console.log('[Long Call Update] ✅ Transaction ID found near label:', checkLine);
          return checkLine;
        }
      }
    }
  }

  console.log('[Long Call Update] ⚠️ "Transaction ID" label found but no numeric value detected');
  return null;
}

// Handle call start event
function handleCallStart() {
  // Check cooldown to prevent duplicate detections
  const now = Date.now();
  if (currentCallState.lastDetectionTime && (now - currentCallState.lastDetectionTime) < DETECTION_COOLDOWN) {
    console.log('[Long Call Update] ⏱️ Cooldown active - ignoring duplicate detection');
    return;
  }

  console.log('[Long Call Update] ✅ Call started - AUTOMATIC TRACKING ENABLED');
  console.log('[Long Call Update] 📍 Detection Frame:', window.name || (window === window.top ? 'MAIN' : 'IFRAME'));
  console.log('[Long Call Update] 📍 Page URL:', window.location.href);

  currentCallState.isActive = true;
  currentCallState.transactionId = extractTransactionId();
  currentCallState.lastDetectionTime = now;
  currentCallState.consecutiveMisses = 0;

  console.log('[Long Call Update] Transaction ID:', currentCallState.transactionId || 'Not detected yet');
  console.log('[Long Call Update] Notifying background script to start timer...');
  console.log('[Long Call Update] 📤 Sending CALL_STARTED message from:', window.name || 'main');

  notifyBackgroundScript('CALL_STARTED', {
    transactionId: currentCallState.transactionId,
    startTime: Date.now()
  });

  // CRITICAL CHANGE: KEEP detection running!
  // We need it to detect when call ends so we can reset for next call!
  console.log('[Long Call Update] ✅ Detection continues running (needed to detect call end)');
  console.log('[Long Call Update] ℹ️ But cooldown prevents duplicate CALL_STARTED messages');
  console.log('[Long Call Update] ℹ️ Will detect when call ends and auto-reset for next call');
}

// Handle call end event
function handleCallEnd() {
  console.log('[Long Call Update] 📴 Call ended');
  const previousTransactionId = currentCallState.transactionId;

  currentCallState.isActive = false;
  currentCallState.transactionId = null;
  currentCallState.lastDetectionTime = null; // Reset cooldown
  currentCallState.consecutiveMisses = 0; // Reset miss counter

  notifyBackgroundScript('CALL_ENDED', {
    transactionId: previousTransactionId
  });

  // Detection is already running (we never stopped it), so just log state reset
  console.log('[Long Call Update] ✅ Call state reset - ready for next call');
  console.log('[Long Call Update] ℹ️ Detection already running - will detect next call automatically');
}

// Send message to background script with error handling
function notifyBackgroundScript(type, data) {
  // Check if extension context is still valid
  try {
    // Try to access chrome.runtime.id - will throw if context invalidated
    if (!chrome.runtime?.id) {
      console.log('[Long Call Update] ⚠️ Extension context lost - stopping script');

      // Stop all timers
      if (pollingTimer) clearInterval(pollingTimer);
      if (observer) observer.disconnect();

      return;
    }

    chrome.runtime.sendMessage({
      type,
      data
    }).catch(error => {
      // Silently handle context invalidation errors (extension was reloaded)
      if (error.message && error.message.includes('context invalidated')) {
        console.log('[Long Call Update] Extension reloaded - old script stopping');

        // Stop all activity
        if (pollingTimer) clearInterval(pollingTimer);
        if (observer) observer.disconnect();
      } else {
        console.error('[Long Call Update] Message error:', error);
      }
    });

  } catch (error) {
    // chrome.runtime is undefined - extension was reloaded
    console.log('[Long Call Update] Extension context lost - script stopping');

    if (pollingTimer) clearInterval(pollingTimer);
    if (observer) observer.disconnect();
  }
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'GET_CALL_STATE') {
    sendResponse(currentCallState);
  } else if (message.type === 'REINITIALIZE') {
    // Extension was reloaded - reinitialize without page refresh
    console.log('[Long Call Update] Reinitializing content script...');
    checkCallStatus(); // Do an immediate check
    sendResponse({ success: true, message: 'Content script reinitialized' });
  } else if (message.type === 'FORCE_CHECK') {
    // Manual trigger to check call status
    console.log('[Long Call Update] Force checking call status...');
    checkCallStatus();
    sendResponse({ success: true, callState: currentCallState });
  } else if (message.type === 'VERIFY_CALL_ACTIVE') {
    // NEW: Actively query DOM to verify if call is still active RIGHT NOW
    console.log('[Long Call Update] 🔍 ACTIVE DOM VERIFICATION REQUESTED');
    console.log('[Long Call Update] Current page URL:', window.location.href);
    console.log('[Long Call Update] Current time:', new Date().toLocaleTimeString());

    const verification = verifyCallActiveNow();

    console.log('[Long Call Update] ✅ Verification complete, sending response...');
    console.log('[Long Call Update] Verification result:', JSON.stringify(verification, null, 2));

    sendResponse(verification);
    return true; // Keep channel open for async response
  } else if (message.type === 'SETTINGS_CONFIGURED') {
    // Settings have been configured - start checking for calls
    console.log('[Long Call Update] ✅ Settings configured - enabling call detection');
    checkCallStatus();
    sendResponse({ success: true });
  }
  return true;
});

// NEW: Actively verify if call is active by checking DOM RIGHT NOW
function verifyCallActiveNow() {
  console.log('[Long Call Update] 🔍 Checking 8X8 DOM for active call indicators...');

  const currentDuration = extractCallDuration();
  const transactionId = extractTransactionId();

  // FIXED: Call is active if EITHER duration OR transactionId exists
  // Per requirement: Auto-reset only if BOTH are missing
  const hasDuration = currentDuration !== null && currentDuration >= 0;
  const hasTransactionId = transactionId &&
                          transactionId !== 'Not found' &&
                          transactionId !== 'Not detected';

  const isActive = hasDuration || hasTransactionId;

  console.log('[Long Call Update] 📊 DOM Verification Results:');
  console.log('[Long Call Update]   Call Duration:', currentDuration !== null ? `${Math.floor(currentDuration/60)}m ${currentDuration%60}s` : '❌ Not found');
  console.log('[Long Call Update]   Transaction ID:', transactionId || '❌ Not found');
  console.log('[Long Call Update]   Has Duration:', hasDuration ? '✅ YES' : '❌ NO');
  console.log('[Long Call Update]   Has TID:', hasTransactionId ? '✅ YES' : '❌ NO');
  console.log('[Long Call Update]   Call Active (Duration OR TID):', isActive ? '✅ YES' : '❌ NO');

  return {
    isActive: isActive,
    duration: currentDuration,
    transactionId: transactionId,
    timestamp: Date.now()
  };
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (observer) {
    observer.disconnect();
  }
  if (pollingTimer) {
    clearInterval(pollingTimer);
  }
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

} // End of duplicate injection guard
