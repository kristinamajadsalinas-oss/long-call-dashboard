// Load saved settings when page loads
document.addEventListener('DOMContentLoaded', loadSettings);

// Save settings when form is submitted
document.getElementById('settingsForm').addEventListener('submit', saveSettings);

// Reset settings when reset button is clicked
document.getElementById('resetBtn').addEventListener('click', resetSettings);

async function loadSettings() {
  try {
    const settings = await chrome.storage.sync.get({
      siebelId: '',
      team: '',
      skillset: 'PS',
      testMode: false
    });

    document.getElementById('siebelId').value = settings.siebelId;
    document.getElementById('team').value = settings.team;

    if (settings.skillset === 'PS') {
      document.getElementById('skillsetPS').checked = true;
    } else {
      document.getElementById('skillsetSTD').checked = true;
    }

    document.getElementById('testMode').checked = settings.testMode;
  } catch (error) {
    console.error('Error loading settings:', error);
    showMessage('Error loading settings', 'error');
  }
}

async function saveSettings(e) {
  e.preventDefault();

  const siebelId = document.getElementById('siebelId').value.trim();
  const team = document.getElementById('team').value.trim();
  const skillset = document.querySelector('input[name="skillset"]:checked').value;
  const testMode = document.getElementById('testMode').checked;

  // Validation
  if (!siebelId || !team) {
    showMessage('Please fill in all required fields', 'error');
    return;
  }

  try {
    await chrome.storage.sync.set({
      siebelId,
      team,
      skillset,
      testMode
    });

    showMessage('Settings saved successfully!', 'success');

    // Notify background script that settings have been updated
    chrome.runtime.sendMessage({ type: 'SETTINGS_UPDATED' });
  } catch (error) {
    console.error('Error saving settings:', error);
    showMessage('Error saving settings', 'error');
  }
}

function resetSettings() {
  if (confirm('Are you sure you want to reset all settings to defaults?')) {
    document.getElementById('siebelId').value = '';
    document.getElementById('team').value = '';
    document.getElementById('skillsetPS').checked = true;
    document.getElementById('testMode').checked = false;

    showMessage('Settings reset. Click "Save Settings" to apply.', 'success');
  }
}

function showMessage(message, type) {
  const statusDiv = document.getElementById('statusMessage');
  statusDiv.textContent = message;
  statusDiv.className = `status-message ${type}`;
  statusDiv.style.display = 'block';

  // Hide message after 5 seconds
  setTimeout(() => {
    statusDiv.style.display = 'none';
  }, 5000);
}
