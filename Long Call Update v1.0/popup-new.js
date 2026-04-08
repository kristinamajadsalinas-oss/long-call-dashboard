let currentCallData = null;
let settings = {
  siebelId: '',
  squad: '',
  skillset: '',
  testMode: false
};

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  attachEventListeners();
  await checkCallStatus();

  // Update every 3 seconds
  setInterval(checkCallStatus, 3000);
});

// Load settings from storage
async function loadSettings() {
  const stored = await chrome.storage.sync.get({
    siebelId: '',
    team: '',
    skillset: '',
    testMode: false
  });

  settings = {
    siebelId: stored.siebelId,
    squad: stored.team,
    skillset: stored.skillset,
    testMode: stored.testMode
  };

  // Populate form
  document.getElementById('siebelId').value = settings.siebelId;
  document.getElementById('squad').value = settings.squad;
  document.getElementById('skillset').value = settings.skillset;
}

// Attach event listeners
function attachEventListeners() {
  document.getElementById('saveBtn').addEventListener('click', saveSettings);
  document.getElementById('copyBtn').addEventListener('click', copyTemplate);

  // Update preview when user types
  document.getElementById('issue').addEventListener('input', updatePreview);
  document.getElementById('reason').addEventListener('input', updatePreview);

  // Update settings when changed
  document.getElementById('siebelId').addEventListener('change', updateSettingsLive);
  document.getElementById('squad').addEventListener('change', updateSettingsLive);
  document.getElementById('skillset').addEventListener('change', updateSettingsLive);
}

// Update settings live (without clicking save)
async function updateSettingsLive() {
  settings.siebelId = document.getElementById('siebelId').value.trim();
  settings.squad = document.getElementById('squad').value.trim();
  settings.skillset = document.getElementById('skillset').value;

  updatePreview();
}

// Save settings
async function saveSettings() {
  const siebelId = document.getElementById('siebelId').value.trim();
  const squad = document.getElementById('squad').value.trim();
  const skillset = document.getElementById('skillset').value;

  if (!siebelId || !squad || !skillset) {
    alert('Please fill in all fields');
    return;
  }

  await chrome.storage.sync.set({
    siebelId,
    team: squad,
    skillset,
    testMode: settings.testMode
  });

  settings = { siebelId, squad, skillset, testMode: settings.testMode };

  // Show saved feedback
  const btn = document.getElementById('saveBtn');
  const originalText = btn.textContent;
  btn.textContent = 'Saved!';
  setTimeout(() => {
    btn.textContent = originalText;
  }, 2000);

  // Notify background
  chrome.runtime.sendMessage({ type: 'SETTINGS_UPDATED' });

  updatePreview();
}

// Check call status
async function checkCallStatus() {
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
    console.error('Error checking call status:', error);
  }
}

// Show no active call state
function showNoCall() {
  const statusIndicator = document.getElementById('statusIndicator');
  const message = document.getElementById('simpleMessage');
  const templateSection = document.getElementById('templateSection');
  const saveSection = document.getElementById('saveSection');

  statusIndicator.textContent = 'Monitoring for calls...';
  statusIndicator.className = 'status-indicator';

  message.style.display = 'block';
  templateSection.style.display = 'none';
  saveSection.style.display = 'block';

  // Clear template fields
  document.getElementById('transactionId').value = '';
  document.getElementById('issue').value = '';
  document.getElementById('reason').value = '';
}

// Show active call state
function showActiveCall() {
  const statusIndicator = document.getElementById('statusIndicator');
  const message = document.getElementById('simpleMessage');
  const templateSection = document.getElementById('templateSection');
  const saveSection = document.getElementById('saveSection');

  if (currentCallData.notified) {
    statusIndicator.textContent = 'Copy and paste the template now';
    statusIndicator.className = 'status-indicator active';
  } else {
    const duration = currentCallData.callDuration || 0;
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    statusIndicator.textContent = `Active call – duration: ${minutes}m ${seconds}s (running)`;
    statusIndicator.className = 'status-indicator active';
  }

  message.style.display = 'none';
  templateSection.style.display = 'block';
  saveSection.style.display = 'none';

  // Populate template
  document.getElementById('transactionId').value = currentCallData.transactionId || '';
  document.getElementById('displaySiebelId').textContent = settings.siebelId || '-';
  document.getElementById('displaySkillset').textContent = settings.skillset || '-';

  const squadDisplay = settings.squad.startsWith('Squad ') ? settings.squad : `Squad ${settings.squad}`;
  document.getElementById('displaySquad').textContent = squadDisplay || '-';

  updatePreview();
}

// Update preview
function updatePreview() {
  const transactionId = document.getElementById('transactionId').value.trim() || '[Not found]';
  const siebelId = settings.siebelId || '[Enter SIEBEL ID]';
  const skillset = settings.skillset || '[Select skillset]';
  const squad = settings.squad ? (settings.squad.startsWith('Squad ') ? settings.squad : `Squad ${settings.squad}`) : '[Enter SQL\'s name]';
  const issue = document.getElementById('issue').value.trim() || '[Please fill in]';
  const reason = document.getElementById('reason').value.trim() || '[Please fill in]';

  const template = `LONG CALL UPDATE

TRANSACTION ID: ${transactionId}
SIEBEL ID: ${siebelId}
SQUAD: ${squad}
SKILLSET: ${skillset}
ISSUE: ${issue}
REASON: ${reason}`;

  document.getElementById('preview').textContent = template;
}

// Copy template
async function copyTemplate() {
  const transactionId = document.getElementById('transactionId').value.trim();
  const issue = document.getElementById('issue').value.trim();
  const reason = document.getElementById('reason').value.trim();

  if (!transactionId) {
    alert('Transaction ID is required');
    return;
  }

  if (!issue || !reason) {
    alert('Please fill in both ISSUE and REASON fields');
    return;
  }

  const previewText = document.getElementById('preview').textContent;

  try {
    await navigator.clipboard.writeText(previewText);

    const btn = document.getElementById('copyBtn');
    const originalText = btn.textContent;
    btn.textContent = 'Copied!';

    setTimeout(() => {
      btn.textContent = originalText;
    }, 2000);

    chrome.runtime.sendMessage({ type: 'TEMPLATE_COPIED' });
  } catch (error) {
    console.error('Copy failed:', error);
    alert('Failed to copy to clipboard');
  }
}

// Update preview when page loads
updatePreview();
