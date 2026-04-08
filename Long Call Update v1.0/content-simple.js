// ═══════════════════════════════════════════════════════════════
// LONG CALL UPDATE - CONTENT SCRIPT v9.0.0 (FIXED)
// Based on working version but with bugs fixed
// ═══════════════════════════════════════════════════════════════

// Prevent multiple script injections
if (window.longCallUpdateContentScriptLoaded) {
  console.log('[Long Call Update] ⚠️ Already loaded - skipping');
} else {
  window.longCallUpdateContentScriptLoaded = true;

console.log('╔════════════════════════════════════════════════════════════════╗');
console.log('║  [Long Call Update] Content Script v9.0.0 LOADED (FIXED)      ║');
console.log('╠════════════════════════════════════════════════════════════════╣');
console.log('║  URL:', window.location.href);
console.log('║  Frame:', window === window.top ? 'MAIN FRAME' : window.name || 'iframe');
console.log('╚════════════════════════════════════════════════════════════════╝');

// State tracking
let currentCallState = {
  isActive: false,
  transactionId: null,
  lastCheck: null,
  lastActiveTime: null // Track when we last detected the call
};

let observer = null;
let debounceTimer = null;
let pollingTimer = null;

// Grace period: Wait 30 seconds of no detection before ending call
// This prevents false "call ended" if page is temporarily refreshing
// The call indicators should ALWAYS be present during active calls
// So 30 seconds is very safe - if they're gone that long, call really ended
const CALL_END_GRACE_PERIOD = 30000; // 30 seconds

// ═══════════════════════════════════════════════════════════════
// INITIALIZE
// ═══════════════════════════════════════════════════════════════

function initialize() {
  console.log('[Long Call Update] Initializing...');

  // Start DOM observer
  startDOMObserver();

  // Poll every 2 seconds
  startPolling();

  // Initial check after 3 seconds
  setTimeout(() => {
    console.log('[Long Call Update] Running initial check...');
    checkCallStatus();
  }, 3000);
}

function startDOMObserver() {
  observer = new MutationObserver(() => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      checkCallStatus();
    }, 500);
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true
  });

  console.log('[Long Call Update] DOM observer started');
}

function startPolling() {
  pollingTimer = setInterval(() => {
    checkCallStatus();
  }, 1000); // Check every 1 second (very frequent!)

  console.log('[Long Call Update] Polling started (every 1 second)');
}

// ═══════════════════════════════════════════════════════════════
// CHECK CALL STATUS
// ═══════════════════════════════════════════════════════════════

function checkCallStatus() {
  const now = Date.now();
  currentCallState.lastCheck = now;

  const isCallActive = detectActiveCall();

  console.log('[Long Call Update] 🔍 Check result:', {
    isCallActive,
    currentIsActive: currentCallState.isActive,
    transactionId: currentCallState.transactionId
  });

  if (isCallActive) {
    // Update last active time
    currentCallState.lastActiveTime = now;

    if (!currentCallState.isActive) {
      // Call JUST started
      console.log('[Long Call Update] 🚀 CALLING handleCallStart() NOW!');
      handleCallStart();
    } else {
      // Call ONGOING - check for Transaction ID updates
      const transactionId = extractTransactionId();
      if (transactionId && transactionId !== currentCallState.transactionId) {
        console.log('[Long Call Update] Transaction ID updated:', transactionId);
        currentCallState.transactionId = transactionId;
        notifyBackgroundScript('CALL_UPDATED', { transactionId });
      }
    }
  } else {
    // Not detecting call anymore
    if (currentCallState.isActive) {
      // Call WAS active - check grace period
      const timeSinceLastActive = now - (currentCallState.lastActiveTime || 0);

      if (timeSinceLastActive >= CALL_END_GRACE_PERIOD) {
        // Grace period expired - call really ended
        console.log('[Long Call Update] Grace period expired - confirming call ended');
        handleCallEnd();
      } else {
        // Still in grace period - don't end yet
        const remaining = Math.ceil((CALL_END_GRACE_PERIOD - timeSinceLastActive) / 1000);
        console.log(`[Long Call Update] ⏳ Grace period: ${remaining}s remaining before call end`);
      }
    }
  }
}

// ═══════════════════════════════════════════════════════════════
// DETECT ACTIVE CALL
// ═══════════════════════════════════════════════════════════════

function detectActiveCall() {
  // Only check on 8x8 domain
  if (!window.location.href.includes('8x8.com')) {
    return false;
  }

  // Exclude history/recordings pages
  const bodyText = document.body?.innerText || '';
  const excludedPages = [
    'interaction history',
    'my recordings',
    'my profile'
  ];

  for (const page of excludedPages) {
    if (bodyText.toLowerCase().includes(page)) {
      return false;
    }
  }

  // Check for navigation buttons (history pages)
  if ((bodyText.includes('Previous') && bodyText.includes('Next'))) {
    return false;
  }

  // METHOD 1: phone-card-test-id (MOST RELIABLE!)
  const phoneCard = document.querySelector('[data-test-id="phone-card-test-id"]');
  if (phoneCard) {
    // Extra logging when call is detected
    if (!currentCallState.isActive) {
      console.log('[Long Call Update] ✅ ACTIVE CALL via phone-card-test-id');
    }
    return true;
  }

  // METHOD 2: interaction-timer
  const timer = document.querySelector('[data-test-id="interaction-timer"]');
  if (timer) {
    const timerText = timer.textContent.trim();
    if (timerText.match(/\d{1,2}:\d{2}/)) {
      if (!currentCallState.isActive) {
        console.log('[Long Call Update] ✅ ACTIVE CALL via interaction-timer:', timerText);
      }
      return true;
    }
  }

  // METHOD 3: hangup-button
  const hangupBtn = document.querySelector('[data-test-id="hangup-button"]');
  if (hangupBtn) {
    if (!currentCallState.isActive) {
      console.log('[Long Call Update] ✅ ACTIVE CALL via hangup-button');
    }
    return true;
  }

  // If we reach here and call was active before, log it
  if (currentCallState.isActive) {
    console.log('[Long Call Update] ⚠️ Call was active but no indicators found!');
    console.log('[Long Call Update]  › phone-card-test-id:', !!phoneCard);
    console.log('[Long Call Update]  › interaction-timer:', !!timer, timer ? timer.textContent : 'N/A');
    console.log('[Long Call Update]  › hangup-button:', !!hangupBtn);
  }

  return false;
}

// ═══════════════════════════════════════════════════════════════
// EXTRACT TRANSACTION ID
// ═══════════════════════════════════════════════════════════════

function extractTransactionId() {
  // Look for <li> containing "Transaction ID"
  const allListItems = document.querySelectorAll('li');

  for (const li of allListItems) {
    const liText = li.textContent || '';

    if (liText.includes('Transaction ID')) {
      // Get all spans in this <li>
      const spans = li.querySelectorAll('span');

      // Look for numeric values
      for (const span of spans) {
        const title = span.getAttribute('title');
        const text = span.textContent.trim();

        // Check title attribute first
        if (title && /^\d{2,8}$/.test(title)) {
          console.log('[Long Call Update] ✅ Transaction ID found (title):', title);
          return title;
        }

        // Check text content
        if (text && /^\d{2,8}$/.test(text) && text !== 'Transaction ID') {
          console.log('[Long Call Update] ✅ Transaction ID found (text):', text);
          return text;
        }
      }
    }
  }

  return null;
}

// ═══════════════════════════════════════════════════════════════
// HANDLE CALL EVENTS
// ═══════════════════════════════════════════════════════════════

function handleCallStart() {
  console.log('[Long Call Update] ✅ CALL STARTED - AUTOMATIC TRACKING ENABLED');

  const now = Date.now();
  currentCallState.isActive = true;
  currentCallState.transactionId = extractTransactionId();
  currentCallState.lastActiveTime = now;

  console.log('[Long Call Update] Transaction ID:', currentCallState.transactionId || 'Not detected yet');

  notifyBackgroundScript('CALL_STARTED', {
    transactionId: currentCallState.transactionId,
    startTime: now
  });

  console.log('[Long Call Update] Timer started automatically!');
}

function handleCallEnd() {
  console.log('[Long Call Update] 📴 CALL ENDED');

  const previousTransactionId = currentCallState.transactionId;

  currentCallState.isActive = false;
  currentCallState.transactionId = null;
  currentCallState.lastActiveTime = null;

  notifyBackgroundScript('CALL_ENDED', {
    transactionId: previousTransactionId
  });

  console.log('[Long Call Update] Call state reset');
}

// ═══════════════════════════════════════════════════════════════
// NOTIFY BACKGROUND
// ═══════════════════════════════════════════════════════════════

function notifyBackgroundScript(type, data) {
  console.log('[Long Call Update] 📤 SENDING MESSAGE TO BACKGROUND:', type, data);

  chrome.runtime.sendMessage({ type, data })
    .then(response => {
      console.log('[Long Call Update] ✅ Message sent successfully! Response:', response);
    })
    .catch(err => {
      console.error('[Long Call Update] ❌ ERROR sending message:', err);
      console.error('[Long Call Update] Message details:', { type, data });

      // Retry once after 1 second
      console.log('[Long Call Update] 🔄 Retrying in 1 second...');
      setTimeout(() => {
        chrome.runtime.sendMessage({ type, data })
          .then(response => {
            console.log('[Long Call Update] ✅ Retry successful! Response:', response);
          })
          .catch(retryErr => {
            console.error('[Long Call Update] ❌ Retry also failed:', retryErr);
          });
      }, 1000);
    });
}

// ═══════════════════════════════════════════════════════════════
// MESSAGE LISTENERS
// ═══════════════════════════════════════════════════════════════

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_CALL_STATE') {
    sendResponse(currentCallState);
  } else if (message.type === 'FORCE_CHECK') {
    checkCallStatus();
    sendResponse({ success: true, callState: currentCallState });
  }
  return true;
});

// ═══════════════════════════════════════════════════════════════
// CLEANUP
// ═══════════════════════════════════════════════════════════════

window.addEventListener('beforeunload', () => {
  if (observer) observer.disconnect();
  if (pollingTimer) clearInterval(pollingTimer);
});

// ═══════════════════════════════════════════════════════════════
// START
// ═══════════════════════════════════════════════════════════════

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}

} // End of duplicate prevention block
