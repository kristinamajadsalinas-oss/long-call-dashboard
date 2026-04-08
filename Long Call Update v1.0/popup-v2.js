let currentCallData = null;
let settings = {
  siebelId: '',
  squad: '',
  skillset: '',
  testMode: false
};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  attachEventListeners();
  await updateUI();

  // Update every 3 seconds
  setInterval(updateUI, 3000);
});

// Load settings
async function loadSettings() {
  const stored = await chrome.storage.sync.get({
    siebelId: '',
    team: '',
    skillset: '',
    testMode: false
  });

  console.log('[Popup] 📥 Loaded from storage:', stored);

  settings = {
    siebelId: stored.siebelId,
    squad: stored.team,
    skillset: stored.skillset,
    testMode: stored.testMode
  };

  console.log('[Popup] ✅ Settings object:', settings);

  // Populate fields
  document.getElementById('siebelId').value = settings.siebelId;
  document.getElementById('squad').value = settings.squad;
  document.getElementById('skillset').value = settings.skillset;
  document.getElementById('testModeCheckbox').checked = settings.testMode;
}

// Attach event listeners
function attachEventListeners() {
  // Settings - only save when button is clicked
  document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);

  // Template
  document.getElementById('issue').addEventListener('input', updatePreview);
  document.getElementById('reason').addEventListener('input', updatePreview);

  // Buttons
  document.getElementById('copyBtn').addEventListener('click', copyTemplate);
  document.getElementById('sendDashboardBtn').addEventListener('click', sendToDashboard);
  document.getElementById('manualTemplateBtn').addEventListener('click', createManualTemplate);
  document.getElementById('settingsBtn').addEventListener('click', openSettings);
  document.getElementById('closeSettingsBtn').addEventListener('click', closeSettings);
  document.getElementById('closeSettingsDoneBtn').addEventListener('click', closeSettings);
  document.getElementById('debugBtn').addEventListener('click', showDebugInfo);

  // Note: closeTemplateBtn and copyBtnTop listeners are attached dynamically when template shows
}

// Dismiss/close template
async function dismissTemplate() {
  try {
    await chrome.runtime.sendMessage({ type: 'DISMISS_CALL' });
    await updateUI();
  } catch (error) {
    console.error('Error dismissing template:', error);
  }
}

// Save settings
async function saveSettings() {
  const saveBtn = document.getElementById('saveSettingsBtn');
  const originalText = saveBtn.textContent;

  try {
    settings.siebelId = document.getElementById('siebelId').value.trim();
    settings.squad = document.getElementById('squad').value.trim();
    settings.skillset = document.getElementById('skillset').value;
    settings.testMode = document.getElementById('testModeCheckbox').checked;

    const dataToSave = {
      siebelId: settings.siebelId,
      team: settings.squad,  // ⚠️ IMPORTANT: Saves 'squad' value to 'team' key for backward compatibility
      skillset: settings.skillset,
      testMode: settings.testMode
    };

    console.log('[Popup] 💾 Saving to storage:', dataToSave);

    // Show saving state
    saveBtn.textContent = 'Saving...';
    saveBtn.disabled = true;

    await chrome.storage.sync.set(dataToSave);
    console.log('[Popup] ✅ Settings saved successfully');

    // Show success state
    saveBtn.textContent = '✓ Saved!';
    saveBtn.style.background = '#28a745';
    saveBtn.style.color = '#FFFFFF';
    saveBtn.style.borderColor = '#28a745';

    chrome.runtime.sendMessage({ type: 'SETTINGS_UPDATED' });
    updatePreview();

    // Reset button after 2 seconds
    setTimeout(() => {
      saveBtn.textContent = originalText;
      saveBtn.disabled = false;
      saveBtn.style.background = '';
      saveBtn.style.color = '';
      saveBtn.style.borderColor = '';
    }, 2000);

  } catch (error) {
    console.error('[Popup] ❌ Error saving settings:', error);
    saveBtn.textContent = '✗ Error';
    saveBtn.style.background = '#dc3545';
    saveBtn.style.color = '#FFFFFF';

    setTimeout(() => {
      saveBtn.textContent = originalText;
      saveBtn.disabled = false;
      saveBtn.style.background = '';
      saveBtn.style.color = '';
      saveBtn.style.borderColor = '';
    }, 2000);
  }
}

// Update UI based on call status
async function updateUI() {
  try {
    const debugInfo = await chrome.runtime.sendMessage({ type: 'GET_DEBUG_INFO' });

    if (debugInfo && debugInfo.activeCallsCount > 0) {
      currentCallData = debugInfo.activeCalls[0];
      showActiveCall();
    } else {
      currentCallData = null;
      showNoCall();
    }
  } catch (error) {
    console.error('Error updating UI:', error);
  }
}

// Show no call state
function showNoCall() {
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const message = document.getElementById('simpleMessage');
  const templateSection = document.getElementById('templateSection');
  const manualSection = document.getElementById('manualTemplateSection');

  statusDot.className = 'status-dot red';
  statusText.textContent = 'No active call';
  message.style.display = 'block';
  templateSection.classList.add('hidden');
  manualSection.style.display = 'block';
}

// Show active call state
function showActiveCall() {
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const message = document.getElementById('simpleMessage');
  const templateSection = document.getElementById('templateSection');
  const manualSection = document.getElementById('manualTemplateSection');

  statusDot.className = 'status-dot green';

  const duration = currentCallData.callDuration || 0;
  const minutes = Math.floor(duration / 60);
  const seconds = duration % 60;

  if (currentCallData.notified) {
    statusText.textContent = `Active call – ${minutes}m ${seconds}s (copy template now)`;
  } else {
    statusText.textContent = `Active call – duration: ${minutes}m ${seconds}s (running)`;
  }

  message.style.display = 'none';
  templateSection.classList.remove('hidden');
  manualSection.style.display = 'none';

  // Attach close template button listener (do it once)
  const closeTemplateBtn = document.getElementById('closeTemplateBtn');
  if (closeTemplateBtn && !closeTemplateBtn.hasAttribute('data-listener-attached')) {
    closeTemplateBtn.addEventListener('click', dismissTemplate);
    closeTemplateBtn.setAttribute('data-listener-attached', 'true');
  }

  // Attach top copy button listener (do it once)
  const copyBtnTop = document.getElementById('copyBtnTop');
  if (copyBtnTop && !copyBtnTop.hasAttribute('data-listener-attached')) {
    copyBtnTop.addEventListener('click', copyTemplate);
    copyBtnTop.setAttribute('data-listener-attached', 'true');
  }

  // Show/hide manual badge
  const manualBadge = document.getElementById('manualBadge');
  if (currentCallData.manual) {
    manualBadge.classList.remove('hidden');
  } else {
    manualBadge.classList.add('hidden');
  }

  // Populate template
  const transactionIdInput = document.getElementById('transactionId');

  // If manual template, make Transaction ID editable
  if (currentCallData.manual) {
    // CRITICAL: Don't clear the field if user is typing!
    // Only set to empty if field doesn't have user input yet
    if (!transactionIdInput.hasAttribute('data-manual-listener')) {
      transactionIdInput.value = ''; // Start empty only first time
    }
    // Otherwise preserve whatever user typed

    transactionIdInput.removeAttribute('readonly');
    transactionIdInput.placeholder = 'Enter Transaction ID manually';
    transactionIdInput.style.background = '#FFFFFF';
    transactionIdInput.style.cursor = 'text';

    // Add input listener for manual TID (attach once)
    if (!transactionIdInput.hasAttribute('data-manual-listener')) {
      transactionIdInput.addEventListener('input', updatePreview);
      transactionIdInput.setAttribute('data-manual-listener', 'true');
    }
  } else {
    // Auto-filled from call - update every time
    transactionIdInput.value = currentCallData.transactionId || '';
    transactionIdInput.setAttribute('readonly', 'true');
    transactionIdInput.placeholder = 'Auto-filled from call';
    transactionIdInput.style.background = '#F8F9FA';
    transactionIdInput.removeAttribute('data-manual-listener');
  }

  document.getElementById('displaySiebelId').textContent = settings.siebelId || '-';
  document.getElementById('displaySkillset').textContent = settings.skillset || '-';

  const squadDisplay = settings.squad ? (settings.squad.startsWith('Squad ') ? settings.squad : `Squad ${settings.squad}`) : '-';
  document.getElementById('displaySquad').textContent = squadDisplay;

  updatePreview();
}

// Update preview
function updatePreview() {
  const transactionIdInput = document.getElementById('transactionId');
  const transactionId = transactionIdInput ? (transactionIdInput.value.trim() || '[Not found]') : '[Not found]';
  const siebelId = settings.siebelId || '[Enter your SIEBEL ID]';
  const skillset = settings.skillset || '[Select skillset]';
  const squad = settings.squad ? (settings.squad.startsWith('Squad ') ? settings.squad : `Squad ${settings.squad}`) : '[Enter your SQL\'s name]';
  const issueEl = document.getElementById('issue');
  const reasonEl = document.getElementById('reason');
  const issue = issueEl ? (issueEl.value.trim() || '[Please fill in]') : '[Please fill in]';
  const reason = reasonEl ? (reasonEl.value.trim() || '[Please fill in]') : '[Please fill in]';

  const template = `LONG CALL UPDATE

TRANSACTION ID: ${transactionId}
SIEBEL ID: ${siebelId}
SQUAD: ${squad}
SKILLSET: ${skillset}
ISSUE: ${issue}
REASON: ${reason}`;

  const previewEl = document.getElementById('preview');
  if (previewEl) {
    previewEl.textContent = template;
  }
}

// Copy template
async function copyTemplate() {
  const transactionIdInput = document.getElementById('transactionId');
  const transactionId = transactionIdInput ? transactionIdInput.value.trim() : '';
  const issueEl = document.getElementById('issue');
  const reasonEl = document.getElementById('reason');
  const issue = issueEl ? issueEl.value.trim() : '';
  const reason = reasonEl ? reasonEl.value.trim() : '';

  if (!transactionId) {
    alert('⚠️ Transaction ID is required.\n\nPlease enter it manually or wait for auto-detection.');
    if (transactionIdInput) {
      transactionIdInput.focus();
    }
    return;
  }

  if (!issue || !reason) {
    alert('⚠️ Please fill in both ISSUE and REASON fields before copying.');
    if (!issue && issueEl) {
      issueEl.focus();
    } else if (reasonEl) {
      reasonEl.focus();
    }
    return;
  }

  const previewText = document.getElementById('preview').textContent;

  try {
    await navigator.clipboard.writeText(previewText);

    // Update both copy buttons
    const btn = document.getElementById('copyBtn');
    const btnTop = document.getElementById('copyBtnTop');

    if (btn) {
      const originalText = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => {
        btn.textContent = originalText;
      }, 2000);
    }

    if (btnTop) {
      const originalText = btnTop.textContent;
      btnTop.textContent = 'Copied!';
      setTimeout(() => {
        btnTop.textContent = originalText;
      }, 2000);
    }

    chrome.runtime.sendMessage({ type: 'TEMPLATE_COPIED' });
  } catch (error) {
    console.error('Copy failed:', error);
    alert('Failed to copy to clipboard');
  }
}

// Send to Dashboard
async function sendToDashboard() {
  console.log('[Dashboard] Send to Dashboard clicked');

  // Validate required fields
  const issueEl = document.getElementById('issue');
  const reasonEl = document.getElementById('reason');
  const issue = issueEl?.value.trim();
  const reason = reasonEl?.value.trim();

  if (!issue || !reason) {
    alert('⚠️ Please fill in both ISSUE and REASON fields before sending.');
    if (!issue && issueEl) {
      issueEl.focus();
    } else if (reasonEl) {
      reasonEl.focus();
    }
    return;
  }

  const btn = document.getElementById('sendDashboardBtn');
  const originalHTML = btn.innerHTML;

  try {
    // Disable button during send
    btn.disabled = true;
    btn.innerHTML = '<span style="font-size: 14px;">⏳</span> Sending...';

    // Collect all data
    const data = {
      timestamp: new Date().toISOString(),
      engineer: settings.siebelId || document.getElementById('displaySiebelId')?.textContent || 'Unknown',
      transactionId: document.getElementById('transactionId')?.value || document.getElementById('displayTransactionId')?.textContent || 'Not detected',
      squad: settings.squad || document.getElementById('displaySquad')?.textContent || 'Unknown',
      skillset: settings.skillset || document.getElementById('displaySkillset')?.textContent || 'Unknown',
      issue: issue,
      reason: reason,
      callDuration: currentCallData?.duration || 'Unknown'
    };

    console.log('[Dashboard] Data to send:', data);

    // Send to Firebase Firestore
    await sendToFirestore(data);

    // Show success message
    btn.innerHTML = '<span style="font-size: 14px;">✅</span> Sent!';

    console.log('[Dashboard] ✅ Successfully sent to Firebase!');

    // Reset button after 2 seconds
    setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = originalHTML;
    }, 2000);

  } catch (error) {
    console.error('[Dashboard] Send failed:', error);
    btn.innerHTML = '<span style="font-size: 14px;">❌</span> Failed';
    alert('❌ Failed to send to dashboard.\n\nPlease use "Copy for Teams" button instead.');

    // Reset button after 2 seconds
    setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = originalHTML;
    }, 2000);
  }
}

// Database integration functions (placeholders - will be configured with your API credentials)

// Placeholder for Airtable integration
async function sendToAirtable(data) {
  // TODO: Add Airtable API call when credentials provided
  // const baseId = 'YOUR_BASE_ID';
  // const apiKey = 'YOUR_API_KEY';
  // const response = await fetch(`https://api.airtable.com/v0/${baseId}/Updates`, {
  //   method: 'POST',
  //   headers: {
  //     'Authorization': `Bearer ${apiKey}`,
  //     'Content-Type': 'application/json'
  //   },
  //   body: JSON.stringify({ records: [{ fields: data }] })
  // });
  // if (!response.ok) throw new Error('Airtable API failed');
  throw new Error('Airtable not configured yet');
}

// Firebase Firestore integration
async function sendToFirestore(data) {
  // Firebase configuration
  const projectId = 'long-call-update-dashboa-233b5';
  const collection = 'updates';

  // Firestore REST API endpoint
  const url = `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents/${collection}`;

  // Convert data to Firestore document format
  const firestoreDoc = {
    fields: {
      timestamp: { timestampValue: data.timestamp },
      engineer: { stringValue: data.engineer },
      transactionId: { stringValue: data.transactionId },
      squad: { stringValue: data.squad },
      skillset: { stringValue: data.skillset },
      issue: { stringValue: data.issue },
      reason: { stringValue: data.reason },
      callDuration: { stringValue: data.callDuration }
    }
  };

  console.log('[Firebase] Sending to Firestore:', url);

  // Send to Firestore
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(firestoreDoc)
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('[Firebase] Error response:', errorText);
    throw new Error(`Firebase error: ${response.status} - ${errorText}`);
  }

  const result = await response.json();
  console.log('[Firebase] Success! Document created:', result.name);

  return result;
}

// Placeholder for Supabase integration
async function sendToSupabase(data) {
  // TODO: Add Supabase API call when credentials provided
  throw new Error('Supabase not configured yet');
}

// Create manual template
async function createManualTemplate() {
  if (!settings.siebelId || !settings.squad || !settings.skillset) {
    alert('Please fill in all Engineer\'s Info fields first (SIEBEL ID, SQUAD, SKILLSET)');
    return;
  }

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'CREATE_MANUAL_TEMPLATE',
      data: {
        transactionId: null,
        startTime: Date.now(),
        manual: true
      }
    });

    if (response && response.success) {
      // Refresh UI to show template
      setTimeout(updateUI, 500);
    }
  } catch (error) {
    console.error('Error creating manual template:', error);
    alert('Error creating manual template');
  }
}

// Settings panel
function openSettings() {
  document.getElementById('settingsPanel').classList.remove('hidden');
}

function closeSettings() {
  document.getElementById('settingsPanel').classList.add('hidden');
}

// Debug info
async function showDebugInfo() {
  const debugDiv = document.getElementById('debugInfo');
  const btn = document.getElementById('debugBtn');

  btn.textContent = 'Loading...';
  btn.disabled = true;

  try {
    const [tabs] = await chrome.tabs.query({ active: true, currentWindow: true });
    const debugData = {
      currentTab: {
        url: tabs?.url || 'N/A',
        title: tabs?.title || 'N/A'
      },
      settings: settings,
      timestamp: new Date().toLocaleString()
    };

    const bgResponse = await chrome.runtime.sendMessage({ type: 'GET_DEBUG_INFO' });
    debugData.background = bgResponse;

    if (tabs?.id) {
      try {
        const contentResponse = await chrome.tabs.sendMessage(tabs.id, { type: 'GET_CALL_STATE' });
        debugData.contentScript = contentResponse;
      } catch (e) {
        debugData.contentScript = { error: 'Content script not responding' };
      }
    }

    debugDiv.textContent = JSON.stringify(debugData, null, 2);
    debugDiv.classList.remove('hidden');
  } catch (error) {
    debugDiv.textContent = `Error: ${error.message}`;
    debugDiv.classList.remove('hidden');
  } finally {
    btn.textContent = 'Refresh Debug Info';
    btn.disabled = false;
  }
}
