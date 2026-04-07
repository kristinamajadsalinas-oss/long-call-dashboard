// DEBUG HELPER - Copy and paste this into the browser console on the 8x8 page
// This will help diagnose why the extension isn't detecting calls

console.clear();
console.log('╔═══════════════════════════════════════════════════════════════╗');
console.log('║           LONG CALL UPDATE - DEBUG HELPER                     ║');
console.log('╚═══════════════════════════════════════════════════════════════╝');
console.log('');

// Check 1: Is content script loaded?
console.log('1️⃣ Content Script Status:');
if (window.longCallUpdateContentScriptVersion) {
  console.log('  ✅ Content script is loaded!');
  console.log('  📌 Version:', window.longCallUpdateContentScriptVersion);
} else {
  console.log('  ❌ Content script NOT loaded!');
  console.log('  💡 Try reloading the extension at edge://extensions/');
}
console.log('');

// Check 2: What frame are we in?
console.log('2️⃣ Frame Information:');
console.log('  • Type:', window === window.top ? 'MAIN FRAME' : 'IFRAME');
console.log('  • Name:', window.name || '(unnamed)');
console.log('  • URL:', window.location.href);
console.log('  • Title:', document.title);
console.log('');

// Check 3: Can we find Transaction ID elements?
console.log('3️⃣ Searching for Transaction ID:');
const allListItems = document.querySelectorAll('li');
console.log('  • Total <li> elements:', allListItems.length);

let found = false;
for (const li of allListItems) {
  const spans = li.querySelectorAll('span');
  for (const span of spans) {
    if (span.textContent.trim() === 'Transaction ID') {
      console.log('  ✅ Found "Transaction ID" label!');
      console.log('  📍 Element:', li);

      // Look for value
      const allSpansInLi = li.querySelectorAll('span');
      for (const valueSpan of allSpansInLi) {
        const title = valueSpan.getAttribute('title');
        const text = valueSpan.textContent.trim();

        if (title && /^\d{4,6}$/.test(title)) {
          console.log('  ✅ Transaction ID VALUE found:', title);
          found = true;
        } else if (text && /^\d{4,6}$/.test(text) && text !== 'Transaction ID') {
          console.log('  ✅ Transaction ID VALUE found:', text);
          found = true;
        }
      }
    }
  }
}

if (!found) {
  console.log('  ❌ Transaction ID NOT found in this frame');
  console.log('  💡 The call details might be in a different iframe');
}
console.log('');

// Check 4: List all iframes
console.log('4️⃣ Iframes on this page:');
const iframes = document.querySelectorAll('iframe');
console.log('  • Total iframes:', iframes.length);
iframes.forEach((iframe, index) => {
  console.log(`  📄 Iframe ${index + 1}:`, iframe.name || iframe.id || '(unnamed)', '→', iframe.src);
});
console.log('');

// Check 5: Search for any 5-digit numbers (potential Transaction IDs)
console.log('5️⃣ Searching for 5-digit numbers (potential Transaction IDs):');
const bodyText = document.body.innerText;
const fiveDigitNumbers = bodyText.match(/\b\d{5}\b/g);
if (fiveDigitNumbers && fiveDigitNumbers.length > 0) {
  console.log('  ✅ Found', fiveDigitNumbers.length, '5-digit numbers:');
  fiveDigitNumbers.slice(0, 10).forEach(num => console.log('    •', num));
  if (fiveDigitNumbers.length > 10) {
    console.log('    ... and', fiveDigitNumbers.length - 10, 'more');
  }
} else {
  console.log('  ❌ No 5-digit numbers found');
}
console.log('');

// Check 6: Force the extension to check for calls
console.log('6️⃣ Triggering extension call check:');
try {
  chrome.runtime.sendMessage({type: 'FORCE_CHECK'}, (response) => {
    if (response && response.callState) {
      console.log('  ✅ Extension responded!');
      console.log('  📊 Call State:', response.callState);
    } else {
      console.log('  ⚠️  Extension responded but no call state');
    }
  });
} catch (error) {
  console.log('  ❌ Error:', error.message);
}
console.log('');

console.log('═══════════════════════════════════════════════════════════════');
console.log('🔍 Debug complete! Check the results above.');
console.log('💡 If Transaction ID is found in an iframe, the content script');
console.log('   needs to run in that specific iframe.');
console.log('═══════════════════════════════════════════════════════════════');
