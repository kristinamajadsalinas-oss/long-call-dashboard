let currentCallData = null;
let cachedSettings = null; // Cache settings to avoid repeated storage reads

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Attach all event listeners AFTER DOM is ready
  attachEventListeners();

  // Initialize the popup
  initializePopup();
});

// Attach all event listeners
function attachEventListeners() {
  // Button event listeners
  document.getElementById('copyBtn').addEventListener('click', copyToClipboard);
  document.getElementById('dismissBtn').addEventListener('click', dismissNotification);
  document.getElementById('closeTemplateBtn').addEventListener('click', closeTemplate);
  document.getElementById('openSettings').addEventListener('click', openSettings);
  document.getElementById('openSettings2').addEventListener('click', openSettings);
  document.getElementById('openSettingsBtn').addEventListener('click', showSettingsView);
  document.getElementById('backBtn').addEventListener('click', showMainView);
  document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
  document.getElementById('debugBtn').addEventListener('click', showDebugInfo);
  document.getElementById('testNowBtn').addEventListener('click', testTemplateNow);

  // Update preview when user types
  document.getElementById('issue').addEventListener('input', updatePreview);
  document.getElementById('reason').addEventListener('input', updatePreview);
  document.getElementById('skillset').addEventListener('change', updatePreview);
  document.getElementById('transactionIdManual').addEventListener('input', updatePreview);
  document.getElementById('manualEditBtn').addEventListener('click', enableManualTransactionId);
}

// Fast settings loader with cache
async function getSettings() {
  if (cachedSettings) {
    return cachedSettings;
  }

  cachedSettings = await chrome.storage.sync.get({
    siebelId: '',
    team: '',
    skillset: 'PS',
    testMode: false
  });

  return cachedSettings;
}

async function initializePopup() {
  try {
    // Speed optimization: Load everything in parallel
    const [callResponse, debugInfo, settings] = await Promise.all([
      chrome.runtime.sendMessage({ type: 'GET_CURRENT_CALL' }),
      chrome.runtime.sendMessage({ type: 'GET_DEBUG_INFO' }),
      getSettings() // Pre-load settings
    ]);

    console.log('Popup initialized:', { callData: callResponse?.callData, debugInfo, settings });

    // NEW BEHAVIOR: Show template immediately if there's ANY active call
    if (debugInfo && debugInfo.activeCallsCount > 0) {
      const activeCall = debugInfo.activeCalls[0];
      currentCallData = activeCall;

      // Show template with live call indicator
      showTemplateState(settings, activeCall.notified);
    } else {
      showNoCallState(settings);
    }
  } catch (error) {
    console.error('Error initializing popup:', error);
    showNoCallState();
  }
}

async function showTemplateState(settings = null, timerReached = false) {
  // CRITICAL: Safety check - ensure currentCallData exists!
  if (!currentCallData) {
    console.error('[Popup] ERROR: showTemplateState called but currentCallData is null!');
    showNoCallState();
    return;
  }

  // Use cached settings or load if not provided
  if (!settings) {
    settings = await getSettings();
  }

  // Check if settings are configured
  if (!settings.siebelId || !settings.team) {
    showSettingsRequired();
    return;
  }

  // Show template state
  document.getElementById('noCallState').style.display = 'none';
  document.getElementById('templateState').style.display = 'block';
  document.getElementById('openSettings2').style.display = 'none';

  // NEW: Update timer info banner based on timer status (preserve X button)
  const timerInfoEl = document.getElementById('timerInfo');

  if (timerReached) {
    timerInfoEl.innerHTML = 'Copy and paste the template now.<button id="closeTemplateBtn" title="Close template" style="position: absolute; top: 12px; right: 12px; background: transparent; border: none; font-size: 18px; cursor: pointer; color: #6c757d; padding: 0; line-height: 1; transition: color 0.2s;">✕</button>';
    timerInfoEl.style.background = '#FFFFFF';
    timerInfoEl.style.border = '1px solid #E9ECEF';
    timerInfoEl.style.color = '#212529';

    // Re-attach event listener after recreating button
    document.getElementById('closeTemplateBtn').addEventListener('click', closeTemplate);
  } else {
    // Active call - show live call data indicator
    const callDuration = currentCallData.callDuration || 0;
    const minutes = Math.floor(callDuration / 60);
    const seconds = callDuration % 60;
    const timerDuration = settings.testMode ? '1 minute' : '22 minutes';

    timerInfoEl.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <span>Active call – duration: ${minutes}m ${seconds}s (running)</span>
        <span class="live-indicator" title="Template is ready to copy. Copy and paste this Long Call Update template at the ${timerDuration} mark or when the call ends." style="background: #6C757D; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 500; cursor: help; white-space: nowrap;">LIVE</span>
      </div>
      <button id="closeTemplateBtn" title="Close template" style="position: absolute; top: 12px; right: 12px; background: transparent; border: none; font-size: 18px; cursor: pointer; color: #6c757d; padding: 0; line-height: 1; transition: color 0.2s;">✕</button>
    `;
    timerInfoEl.style.background = '#FFFFFF';
    timerInfoEl.style.border = '1px solid #E9ECEF';
    timerInfoEl.style.color = '#495057';

    // Re-attach event listener after recreating button
    document.getElementById('closeTemplateBtn').addEventListener('click', closeTemplate);
  }

  // NEW: Update live call duration every 3 seconds (if not manual template and timer not reached)
  if (!currentCallData.manual && !timerReached) {
    const updateInterval = setInterval(async () => {
      try {
        const debugInfo = await chrome.runtime.sendMessage({ type: 'GET_DEBUG_INFO' });

        if (debugInfo.activeCallsCount === 0) {
          // Call ended - refresh popup
          console.log('[Popup] Call ended - refreshing popup');
          clearInterval(updateInterval);
          initializePopup();
        } else {
          // Update live duration in banner
          const activeCall = debugInfo.activeCalls[0];
          const callDuration = activeCall.callDuration || 0;
          const minutes = Math.floor(callDuration / 60);
          const seconds = callDuration % 60;
          const timerDuration = settings.testMode ? '1 minute' : '22 minutes';

          const timerInfoEl = document.getElementById('timerInfo');
          if (timerInfoEl && !activeCall.notified) {
            timerInfoEl.innerHTML = `
              <div style="display: flex; align-items: center; gap: 8px;">
                <span>Active call – duration: ${minutes}m ${seconds}s (running)</span>
                <span class="live-indicator" title="Template is ready to copy. Copy and paste this Long Call Update template at the ${timerDuration} mark or when the call ends." style="background: #6C757D; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 500; cursor: help; white-space: nowrap;">LIVE (!)</span>
              </div>
              <button id="closeTemplateBtn" title="Close template" style="position: absolute; top: 12px; right: 12px; background: transparent; border: none; font-size: 18px; cursor: pointer; color: #6c757d; padding: 0; line-height: 1; transition: color 0.2s;">✕</button>
            `;
            timerInfoEl.style.background = '#FFFFFF';
            timerInfoEl.style.border = '1px solid #E9ECEF';
            timerInfoEl.style.color = '#495057';

            // Re-attach event listener
            document.getElementById('closeTemplateBtn').addEventListener('click', closeTemplate);
          } else if (activeCall.notified) {
            // Timer reached - update banner
            timerInfoEl.innerHTML = 'Copy and paste the template now.<button id="closeTemplateBtn" title="Close template" style="position: absolute; top: 12px; right: 12px; background: transparent; border: none; font-size: 18px; cursor: pointer; color: #6c757d; padding: 0; line-height: 1; transition: color 0.2s;">✕</button>';
            timerInfoEl.style.background = '#FFFFFF';
            timerInfoEl.style.border = '1px solid #E9ECEF';
            timerInfoEl.style.color = '#212529';

            // Re-attach event listener
            document.getElementById('closeTemplateBtn').addEventListener('click', closeTemplate);

            clearInterval(updateInterval); // Stop updating
          }
        }
      } catch (error) {
        console.error('[Popup] Error updating duration:', error);
      }
    }, 3000);

    window.templateMonitorInterval = updateInterval;
  }

  // Update instructions banner based on timer status and manual template
  const instructionsBanner = document.getElementById('instructionsBanner');

  if (currentCallData.manual) {
    // Manual template indicator
    instructionsBanner.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <span style="background: #6C757D; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 500;">MANUAL TEMPLATE</span>
        <span style="font-size: 11px; color: #6C757D;">Created without active call</span>
      </div>
      <strong style="color: #212529;">1.</strong> Enter Transaction ID manually<br>
      <strong style="color: #212529;">2.</strong> Fill Issue & Reason<br>
      <strong style="color: #212529;">3.</strong> Copy & paste to Teams
    `;
  } else if (timerReached) {
    instructionsBanner.innerHTML = `
      <strong style="color: #212529;">1.</strong> Verify Transaction ID<br>
      <strong style="color: #212529;">2.</strong> Fill Issue & Reason<br>
      <strong style="color: #212529;">3.</strong> Copy & paste to Teams
    `;
  } else {
    const timerDuration = settings.testMode ? '1 minute' : '22 minutes';
    instructionsBanner.innerHTML = `
      <strong style="color: #212529;">Template Ready:</strong> Transaction ID is autofilled from the active call.<br>
      <strong style="color: #212529;">Next Steps:</strong> Fill in Issue & Reason fields, then copy the template at the ${timerDuration} mark or when the call ends.
    `;
  }

  // Populate fields - show auto-detected Transaction ID or allow manual input
  const transactionId = currentCallData.transactionId;
  const transactionIdDisplay = document.getElementById('transactionId');
  const transactionIdManual = document.getElementById('transactionIdManual');
  const transactionHelpText = document.getElementById('transactionHelpText');
  const manualEditBtn = document.getElementById('manualEditBtn');

  if (transactionId && transactionId !== 'Not found' && transactionId !== 'Not detected' && transactionId !== null) {
    // Auto-detected successfully
    transactionIdDisplay.textContent = transactionId;
    transactionIdDisplay.style.backgroundColor = '#F8F9FA';
    transactionIdDisplay.style.color = '#212529';
    transactionIdManual.style.display = 'none';
    transactionHelpText.style.display = 'none';
    manualEditBtn.textContent = 'Edit';
    console.log('[Long Call Update] ✅ Transaction ID auto-detected:', transactionId);
  } else {
    // Not auto-detected - show manual input immediately
    transactionIdDisplay.textContent = 'Not auto-detected';
    transactionIdDisplay.style.backgroundColor = '#F8F9FA';
    transactionIdDisplay.style.color = '#6C757D';
    transactionIdDisplay.style.display = 'none'; // Hide the display, show input
    transactionIdManual.style.display = 'block';
    transactionHelpText.style.display = 'block';
    manualEditBtn.style.display = 'none';
    setTimeout(() => transactionIdManual.focus(), 100);
    console.log('[Long Call Update] ⚠️ Transaction ID not auto-detected, showing manual input');
  }

  document.getElementById('siebelId').textContent = settings.siebelId;
  // Format team as "Squad [name]"
  const teamDisplay = settings.team.startsWith('Squad ') ? settings.team : `Squad ${settings.team}`;
  document.getElementById('team').textContent = teamDisplay;
  document.getElementById('skillset').value = settings.skillset;

  // Update call duration
  if (currentCallData && currentCallData.startTime) {
    updateCallDuration(currentCallData.startTime);
    setInterval(() => updateCallDuration(currentCallData.startTime), 1000);
  }

  // Update preview
  updatePreview();
}

// Store original HTML content on first load
let originalNoCallHTML = null;

async function showNoCallState(settings = null) {
  document.getElementById('noCallState').style.display = 'block';
  document.getElementById('templateState').style.display = 'none';
  document.getElementById('openSettings2').style.display = 'none';

  const noCallDiv = document.getElementById('noCallState');

  // Save original HTML on first run
  if (!originalNoCallHTML) {
    originalNoCallHTML = noCallDiv.innerHTML;
  } else {
    // Restore original HTML (in case it was replaced by tracking/settings views)
    noCallDiv.innerHTML = originalNoCallHTML;
  }

  // Use cached settings or load if not provided
  if (!settings) {
    settings = await getSettings();
  }

  // Update timer duration based on settings
  const durationText = settings.testMode ? '1 minute' : '22 minutes';
  const timerDurationEl = document.getElementById('timerDuration');
  if (timerDurationEl) {
    timerDurationEl.textContent = durationText;
  }

  // Re-attach event listeners after restoring HTML
  const testBtn = document.getElementById('testNowBtn');
  if (testBtn) {
    testBtn.addEventListener('click', testTemplateNow);
  }

  const settingsBtn = document.getElementById('openSettings');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', openSettings);
  }

  // Add call detection status indicator
  await showCallDetectionStatus();
}

async function showCallDetectionStatus() {
  try {
    // Query current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab || !tab.url || !tab.url.includes('8x8.com')) {
      // Not on 8x8 page
      updateDetectionIndicator('⚠️ Not on 8x8 page');
      return;
    }

    // Try to ping content script
    try {
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_CALL_STATE' });

      if (response && response.isActive) {
        updateDetectionIndicator('✅ Call detected! Starting timer...');
      } else {
        updateDetectionIndicator('⏳ Monitoring for calls...');
      }
    } catch (error) {
      // Content script not responding
      updateDetectionIndicator('❌ Content script not loaded');
    }
  } catch (error) {
    console.error('Error checking detection status:', error);
  }
}

function updateDetectionIndicator(message) {
  const noCallDiv = document.getElementById('noCallState');

  // Check if indicator already exists
  let indicator = noCallDiv.querySelector('.detection-indicator');

  if (!indicator) {
    // Create indicator
    indicator = document.createElement('div');
    indicator.className = 'detection-indicator';
    indicator.style.cssText = `
      margin: 15px 0;
      padding: 10px 15px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 400;
      text-align: center;
      border: 1px solid #E9ECEF;
      background: #F8F9FA;
      color: #495057;
    `;

    // Insert before the h2 element
    const titleEl = noCallDiv.querySelector('h2');
    if (titleEl) {
      titleEl.parentNode.insertBefore(indicator, titleEl);
    } else {
      noCallDiv.insertBefore(indicator, noCallDiv.firstChild);
    }
  }

  // Update indicator with message only (no color coding)
  indicator.textContent = message;
}

async function showTrackingState(callData, settings = null) {
  document.getElementById('noCallState').style.display = 'block';
  document.getElementById('templateState').style.display = 'none';
  document.getElementById('openSettings2').style.display = 'none';

  // Use cached settings if not provided
  if (!settings) {
    settings = await getSettings();
  }

  const noCallDiv = document.getElementById('noCallState');

  // Determine timer duration message
  const timerDuration = settings.testMode ? '1 minute' : '22 minutes';

  // Update the display (minimal colors with simple glyph icon)
  noCallDiv.innerHTML = `
    <div style="text-align: center; padding: 30px 20px;">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin: 0 auto 15px; display: block;">
        <path d="M3 5.5C3 14.0604 9.93959 21 18.5 21c.462 0 .657-.126.848-.315.191-.19.402-.561.402-1.185v-2.25c0-.539-.182-.948-.377-1.237-.195-.29-.466-.511-.743-.683a18.28 18.28 0 0 1-.623-.31l-.03-.016-.006-.003h-.002L17.5 16.5l-.469-1.499.002.001.007.003.024.01a7.7 7.7 0 0 0 .367.14c.23.082.527.189.818.284.145.047.279.09.389.121.055.016.101.028.135.036l.018.004-.018-.004a.384.384 0 0 0-.018-.004 1.276 1.276 0 0 0-.135-.036 5.735 5.735 0 0 0-.389-.121 16.788 16.788 0 0 0-.818-.284 9.2 9.2 0 0 0-.367-.14l-.024-.01-.007-.003-.002-.001.469-1.499.469 1.499c-.002 0-.003-.001-.004-.002a.628.628 0 0 1-.063-.04 1.35 1.35 0 0 1-.108-.082c-.077-.064-.168-.15-.259-.252a5.28 5.28 0 0 1-.623-.752c-.364-.526-.748-1.29-.748-2.373V5.5c0-.624.211-.995.402-1.185.19-.19.386-.315.848-.315C14.0604 4 7.12 10.9396 7.12 19.5c0 .462.126.657.315.848.19.191.561.402 1.185.402h2.25c.539 0 .948-.182 1.237-.377.29-.195.511-.466.683-.743.172-.277.298-.58.372-.865.074-.285.1-.542.1-.76 0-.218-.026-.475-.1-.76-.074-.285-.2-.588-.372-.865a3.376 3.376 0 0 0-.683-.743c-.29-.195-.698-.377-1.237-.377H8.62c-.624 0-.995.211-1.185.402-.19.19-.315.386-.315.848C7.12 10.9396 14.0604 4 22.62 4c.462 0 .657.126.848.315.191.19.402.561.402 1.185v2.25z" fill="#ADB5BD"/>
      </svg>
      <h3 style="color: #212529; margin: 0 0 15px 0; font-size: 20px; font-weight: 500;">Active Call Detected</h3>
      <p style="font-size: 14px; margin-bottom: 20px; line-height: 1.6; color: #495057;">
        The template will appear when your call reaches <strong>${timerDuration}</strong>.
      </p>
      <div style="background: #F8F9FA; border: 1px solid #E9ECEF; border-radius: 6px; padding: 20px; margin-bottom: 20px;">
        <p style="font-size: 13px; margin: 0 0 10px 0; color: #6C757D; font-weight: 500;">TIME REMAINING</p>
        <div id="countdown" style="font-size: 42px; font-weight: 500; color: #212529; margin: 0;">--:--</div>
      </div>
      <p style="font-size: 12px; color: #6C757D; margin-bottom: 20px;">You'll be notified automatically—no need to keep this window open.</p>
      <hr style="margin: 20px 0; border: none; border-top: 1px solid #E9ECEF;">
      <button class="btn-settings" id="cancelTrackingBtn" style="background-color: #6C757D; color: white; font-size: 13px;">
        Cancel Tracking
      </button>
    </div>
  `;

  // Attach cancel button event
  const cancelBtn = document.getElementById('cancelTrackingBtn');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', async () => {
      cancelBtn.textContent = 'Cancelling...';
      cancelBtn.disabled = true;
      await chrome.runtime.sendMessage({ type: 'DISMISS_CALL' });
      setTimeout(() => {
        window.close();
      }, 300);
    });
  }

  // Update countdown AND continuously check for template
  let templateCheckInterval = null;

  async function updateCountdown() {
    const settings = await chrome.storage.sync.get({ testMode: false });
    const targetTime = settings.testMode ? 1 * 60 * 1000 : 22 * 60 * 1000;
    const elapsed = Date.now() - callData.startTime;
    const remaining = Math.max(0, targetTime - elapsed);
    const remainingSeconds = Math.floor(remaining / 1000);
    const remainingMinutes = Math.floor(remainingSeconds / 60);
    const remainingSecs = remainingSeconds % 60;

    const countdownEl = document.getElementById('countdown');
    if (countdownEl) {
      countdownEl.textContent = `${remainingMinutes}:${remainingSecs.toString().padStart(2, '0')}`;

      if (remaining > 0) {
        setTimeout(updateCountdown, 1000);
      } else {
        // Timer expired! Show "Ready!" temporarily
        countdownEl.textContent = 'Ready!';
        countdownEl.style.color = '#212529';

        // Start checking every 2 seconds for template
        if (!templateCheckInterval) {
          console.log('[Popup] Starting continuous template check...');
          templateCheckInterval = setInterval(async () => {
            console.log('[Popup] Checking if template is ready...');
            const response = await chrome.runtime.sendMessage({ type: 'GET_CURRENT_CALL' });
            if (response && response.callData) {
              // Template is ready!
              console.log('[Popup] ✅ Template ready! Showing it now...');
              clearInterval(templateCheckInterval);
              templateCheckInterval = null;
              initializePopup(); // Refresh to show template
            } else {
              console.log('[Popup] ⏳ Template not ready yet, checking again...');
            }
          }, 2000); // Check every 2 seconds
        }
      }
    }
  }

  updateCountdown();
}

function showSettingsRequired() {
  document.getElementById('noCallState').style.display = 'block';
  document.getElementById('templateState').style.display = 'none';
  document.getElementById('openSettings2').style.display = 'none';

  const noCallDiv = document.getElementById('noCallState');
  noCallDiv.innerHTML = `
    <div style="text-align: center; padding: 30px 20px;">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin: 0 auto 15px; display: block;">
        <path d="M12 2.25c.621 0 1.125.504 1.125 1.125v1.5a1.125 1.125 0 0 1-2.25 0v-1.5c0-.621.504-1.125 1.125-1.125ZM5.636 5.636a1.125 1.125 0 0 1 1.591 0l1.061 1.06a1.125 1.125 0 0 1-1.591 1.592l-1.06-1.061a1.125 1.125 0 0 1 0-1.591ZM12 7.5A4.5 4.5 0 1 0 12 16.5 4.5 4.5 0 0 0 12 7.5Zm-6.75 4.5a1.125 1.125 0 0 0-1.125-1.125h-1.5a1.125 1.125 0 0 0 0 2.25h1.5c.621 0 1.125-.504 1.125-1.125Zm14.625-1.125a1.125 1.125 0 0 1 0 2.25h-1.5a1.125 1.125 0 0 1 0-2.25h1.5Zm-1.364 5.489a1.125 1.125 0 0 0-1.591 1.591l1.06 1.061a1.125 1.125 0 0 0 1.592-1.591l-1.061-1.061Zm-10.758 0l-1.061 1.061a1.125 1.125 0 0 0 1.591 1.591l1.061-1.06a1.125 1.125 0 0 0-1.591-1.592ZM12 18.375a1.125 1.125 0 0 1 1.125 1.125v1.5a1.125 1.125 0 0 1-2.25 0v-1.5c0-.621.504-1.125 1.125-1.125Z" fill="#ADB5BD"/>
      </svg>
      <h3 style="margin: 0 0 15px 0; font-size: 20px; font-weight: 500; color: #212529;">Setup Required</h3>
      <p style="font-size: 14px; margin-bottom: 25px; line-height: 1.6;">
        Please configure your <strong>SIEBEL ID</strong> and <strong>TEAM</strong> before using the extension.
      </p>
      <button class="btn-settings" id="openSettingsFromRequired" style="background-color: #D71921; color: white; border-color: #D71921; padding: 12px 24px; font-size: 14px;">
        Open Settings
      </button>
    </div>
  `;

  // Re-attach event listener
  document.getElementById('openSettingsFromRequired').addEventListener('click', showSettingsView);
}

function updateCallDuration(startTime) {
  const now = Date.now();
  const duration = Math.floor((now - startTime) / 1000);
  const minutes = Math.floor(duration / 60);
  const seconds = duration % 60;

  // Call duration display removed from UI - no longer needed
  // (Badge and popup states now show call status clearly)
}

function updatePreview() {
  // Get transaction ID - use manual input if visible, otherwise use auto-detected
  const manualInput = document.getElementById('transactionIdManual');
  const autoDetected = document.getElementById('transactionId');

  let transactionId;
  if (manualInput.style.display !== 'none' && manualInput.value.trim()) {
    transactionId = manualInput.value.trim();
  } else if (autoDetected.style.display !== 'none') {
    transactionId = autoDetected.textContent;
    if (transactionId === 'Not auto-detected' || transactionId === '-') {
      transactionId = '[Not found]';
    }
  } else {
    transactionId = '[Not found]';
  }

  const siebelId = document.getElementById('siebelId').textContent;
  const skillset = document.getElementById('skillset').value;
  const team = document.getElementById('team').textContent;
  const issue = document.getElementById('issue').value.trim();
  const reason = document.getElementById('reason').value.trim();

  const template = `TRANSACTION ID: ${transactionId}
SIEBEL ID: ${siebelId}
SKILLSET: ${skillset}
SQUAD: ${team}
ISSUE: ${issue || '[Please fill in]'}
REASON: ${reason || '[Please fill in]'}`;

  document.getElementById('preview').textContent = template;
}

async function copyToClipboard() {
  // Get transaction ID from either auto-detected or manual input
  const manualInput = document.getElementById('transactionIdManual');
  const autoDetected = document.getElementById('transactionId');

  let transactionId;
  if (manualInput.style.display !== 'none') {
    transactionId = manualInput.value.trim();
  } else {
    transactionId = autoDetected.textContent;
  }

  const issue = document.getElementById('issue').value.trim();
  const reason = document.getElementById('reason').value.trim();

  // Validate all required fields
  if (!transactionId || transactionId === 'Not auto-detected' || transactionId === '-' || transactionId === '[Not found]') {
    alert('⚠️ Transaction ID is required.\n\n📋 Please click "Edit" to enter it manually.');
    enableManualTransactionId();
    return;
  }

  if (!issue || !reason) {
    alert('⚠️ Please fill in both ISSUE and REASON fields before copying.');
    if (!issue) {
      document.getElementById('issue').focus();
    } else {
      document.getElementById('reason').focus();
    }
    return;
  }

  const previewText = document.getElementById('preview').textContent;

  try {
    await navigator.clipboard.writeText(previewText);

    // Update button to show success
    const copyBtn = document.getElementById('copyBtn');
    const originalText = copyBtn.textContent;
    copyBtn.textContent = 'Copied!';
    copyBtn.classList.add('copied');

    // Reset button after 2 seconds
    setTimeout(() => {
      copyBtn.textContent = originalText;
      copyBtn.classList.remove('copied');
    }, 2000);

    // Log analytics
    chrome.runtime.sendMessage({ type: 'TEMPLATE_COPIED' });
  } catch (error) {
    console.error('Failed to copy:', error);
    alert('Failed to copy to clipboard. Please try again.');
  }
}

async function dismissNotification() {
  try {
    console.log('Dismissing notification/call...');

    // Clear the call data
    await chrome.runtime.sendMessage({ type: 'DISMISS_CALL' });

    // Show confirmation briefly
    const btn = document.getElementById('dismissBtn');
    if (btn) {
      btn.textContent = 'Cancelled!';
      btn.disabled = true;
    }

    // Close popup after a moment
    setTimeout(() => {
      window.close();
    }, 500);
  } catch (error) {
    console.error('Error dismissing notification:', error);
    window.close();
  }
}

// Close template and return to monitoring (for wrap-up time)
async function closeTemplate() {
  try {
    console.log('Closing template - returning to monitoring...');

    // Dismiss the call in background
    await chrome.runtime.sendMessage({ type: 'DISMISS_CALL' });

    // Clear current call data
    currentCallData = null;

    // Get settings and show "No Active Call" state
    const settings = await getSettings();
    showNoCallState(settings);

    console.log('✅ Template closed - returned to monitoring');
  } catch (error) {
    console.error('Error closing template:', error);
    // Still try to show no call state even if dismiss fails
    showNoCallState();
  }
}

function openSettings() {
  showSettingsView();
}

async function showSettingsView() {
  // Load current settings
  const settings = await chrome.storage.sync.get({
    siebelId: '',
    team: '',
    skillset: 'PS',
    testMode: false
  });

  // Populate form
  document.getElementById('settingsSiebelId').value = settings.siebelId;
  document.getElementById('settingsTeam').value = settings.team;
  document.getElementById('settingsSkillset').value = settings.skillset;
  document.getElementById('settingsTestMode').checked = settings.testMode;

  // Toggle views
  document.querySelector('.main-view').classList.add('hidden');
  document.getElementById('settingsView').classList.add('active');
}

function showMainView() {
  // Toggle views back
  document.querySelector('.main-view').classList.remove('hidden');
  document.getElementById('settingsView').classList.remove('active');

  // Reload the popup to reflect any changes
  initializePopup();
}

async function saveSettings() {
  const siebelId = document.getElementById('settingsSiebelId').value.trim();
  const team = document.getElementById('settingsTeam').value.trim();
  const skillset = document.getElementById('settingsSkillset').value;
  const testMode = document.getElementById('settingsTestMode').checked;

  // Validation
  if (!siebelId || !team) {
    showSettingsStatus('Please fill in all required fields', 'error');
    return;
  }

  try {
    await chrome.storage.sync.set({
      siebelId,
      team,
      skillset,
      testMode
    });

    // Clear settings cache so changes take effect immediately
    cachedSettings = null;

    showSettingsStatus('Settings saved successfully!', 'success');

    // Notify background script
    chrome.runtime.sendMessage({ type: 'SETTINGS_UPDATED' });

    // Return to main view after 1 second
    setTimeout(() => {
      showMainView();
    }, 1000);
  } catch (error) {
    console.error('Error saving settings:', error);
    showSettingsStatus('Error saving settings', 'error');
  }
}

function showSettingsStatus(message, type) {
  const statusDiv = document.getElementById('settingsStatus');
  statusDiv.textContent = message;
  statusDiv.className = `settings-status ${type}`;

  // Hide after 3 seconds
  setTimeout(() => {
    statusDiv.className = 'settings-status';
  }, 3000);
}

function enableManualTransactionId() {
  const transactionIdDisplay = document.getElementById('transactionId');
  const transactionIdManual = document.getElementById('transactionIdManual');
  const transactionHelpText = document.getElementById('transactionHelpText');
  const manualEditBtn = document.getElementById('manualEditBtn');
  const transactionIdDisplayWrapper = document.getElementById('transactionIdDisplay');

  // Get the current auto-detected value (if any)
  const currentValue = transactionIdDisplay.textContent;

  // Hide the display, show the manual input
  transactionIdDisplayWrapper.style.display = 'none';
  transactionIdManual.style.display = 'block';
  transactionHelpText.style.display = 'block';

  // If there was an auto-detected value, pre-fill it
  if (currentValue && currentValue !== 'Not auto-detected' && currentValue !== '-') {
    transactionIdManual.value = currentValue;
  }

  // Focus the input
  setTimeout(() => transactionIdManual.focus(), 100);

  console.log('[Long Call Update] Switched to manual Transaction ID input');
}

async function showDebugInfo() {
  const debugDiv = document.getElementById('debugInfo');
  const btn = document.getElementById('debugBtn');

  btn.textContent = 'Loading...';
  btn.disabled = true;

  try {
    // Get debug info from background and content scripts
    const [tabs] = await chrome.tabs.query({ active: true, currentWindow: true });
    const debugData = {
      currentTab: {
        url: tabs?.url || 'N/A',
        title: tabs?.title || 'N/A'
      },
      timestamp: new Date().toLocaleString()
    };

    // Try to get call state from background
    try {
      const bgResponse = await chrome.runtime.sendMessage({ type: 'GET_DEBUG_INFO' });
      debugData.background = bgResponse;
    } catch (e) {
      debugData.background = { error: e.message };
    }

    // Try to get state from content script
    if (tabs?.id) {
      try {
        const contentResponse = await chrome.tabs.sendMessage(tabs.id, { type: 'GET_CALL_STATE' });
        debugData.contentScript = contentResponse;
      } catch (e) {
        debugData.contentScript = { error: 'Content script not responding. Make sure you are on the 8x8 page.' };
      }
    }

    // Display debug info
    debugDiv.textContent = JSON.stringify(debugData, null, 2);
    debugDiv.style.display = 'block';
  } catch (error) {
    debugDiv.textContent = `Error getting debug info:\n${error.message}`;
    debugDiv.style.display = 'block';
  } finally {
    btn.textContent = 'Refresh Debug Info';
    btn.disabled = false;
  }
}

async function testTemplateNow() {
  const btn = document.getElementById('testNowBtn');

  btn.textContent = 'Opening...';
  btn.disabled = true;

  try {
    // Check if settings are configured
    const settings = await chrome.storage.sync.get({
      siebelId: '',
      team: '',
      skillset: 'PS'
    });

    if (!settings.siebelId || !settings.team) {
      alert('Please configure your SIEBEL ID and TEAM in Settings first!');
      btn.textContent = 'Manual Template';
      btn.disabled = false;
      document.getElementById('openSettings').click();
      return;
    }

    // Create manual template in BACKGROUND so it persists across popup opens/closes
    const response = await chrome.runtime.sendMessage({
      type: 'CREATE_MANUAL_TEMPLATE',
      data: {
        transactionId: null, // Force manual input
        startTime: Date.now(),
        manual: true
      }
    });

    if (response && response.success) {
      // Reload popup to show the template
      initializePopup();
    } else {
      alert('Error creating manual template');
      btn.textContent = 'Manual Template';
      btn.disabled = false;
    }

    return;

    // Focus on Transaction ID input field for manual entry
    setTimeout(() => {
      const transactionIdInput = document.getElementById('transactionIdManual');
      if (transactionIdInput) {
        transactionIdInput.focus();
      }
    }, 100);

  } catch (error) {
    console.error('Error opening manual template:', error);
    alert('Error: ' + error.message);
    btn.textContent = 'Manual Template';
    btn.disabled = false;
  }
}
