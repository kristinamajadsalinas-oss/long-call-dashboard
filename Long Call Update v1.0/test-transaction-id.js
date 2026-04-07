// ========================================
// TRANSACTION ID DETECTION TEST SCRIPT
// ========================================
// Copy and paste this entire script into the browser console (F12)
// while you have an active call with a Transaction ID visible

console.clear();
console.log('═══════════════════════════════════════════════════');
console.log('   TRANSACTION ID DETECTION TEST');
console.log('═══════════════════════════════════════════════════');
console.log('');

// Test 1: Check current frame
console.log('📍 FRAME INFORMATION:');
console.log('  • Frame type:', window === window.top ? 'MAIN FRAME' : 'IFRAME');
console.log('  • Frame name:', window.name || '(unnamed)');
console.log('  • Frame ID:', window.frameElement?.id || '(no ID)');
console.log('  • URL:', window.location.href);
console.log('');

// Test 2: Count elements
console.log('📊 PAGE ELEMENTS:');
console.log('  • Total <li> elements:', document.querySelectorAll('li').length);
console.log('  • Total <span> elements:', document.querySelectorAll('span').length);
console.log('');

// Test 3: Look for "Transaction ID" label
console.log('🔍 SEARCHING FOR "Transaction ID" LABEL:');
let foundTransactionIdLabel = false;
let transactionIdValue = null;

document.querySelectorAll('li').forEach((li, index) => {
  const spans = li.querySelectorAll('span');

  spans.forEach(span => {
    const text = span.textContent.trim();

    if (text === 'Transaction ID') {
      console.log('  ✅ FOUND "Transaction ID" label in <li> #' + index);
      console.log('     HTML:', li.outerHTML.substring(0, 200) + '...');
      foundTransactionIdLabel = true;

      // Try to find the value
      const allSpansInLi = li.querySelectorAll('span');
      allSpansInLi.forEach(valueSpan => {
        const title = valueSpan.getAttribute('title');
        const value = valueSpan.textContent.trim();

        // Check if it's a 5-digit number
        if (title && /^\d{5}$/.test(title)) {
          console.log('     🎯 Transaction ID VALUE (from title):', title);
          transactionIdValue = title;
        } else if (value && /^\d{5}$/.test(value) && value !== 'Transaction ID') {
          console.log('     🎯 Transaction ID VALUE (from text):', value);
          transactionIdValue = value;
        }
      });
    }
  });
});

if (!foundTransactionIdLabel) {
  console.log('  ❌ "Transaction ID" label NOT found');
}
console.log('');

// Test 4: Look for ANY 5-digit numbers
console.log('🔢 SEARCHING FOR 5-DIGIT NUMBERS:');
const bodyText = document.body.innerText;
const fiveDigitNumbers = bodyText.match(/\b\d{5}\b/g);

if (fiveDigitNumbers && fiveDigitNumbers.length > 0) {
  console.log('  ✅ Found', fiveDigitNumbers.length, '5-digit number(s):');
  fiveDigitNumbers.forEach((num, i) => {
    console.log('     ' + (i + 1) + '.', num);
  });
} else {
  console.log('  ❌ No 5-digit numbers found on this page');
}
console.log('');

// Test 5: Look for call panel fields
console.log('📋 SEARCHING FOR CALL PANEL FIELDS:');
const callFields = ['Transaction ID', 'Phone number', 'Queue', 'Caller name', 'Channel name', 'Wait time'];
const foundFields = [];

document.querySelectorAll('span').forEach(span => {
  const text = span.textContent.trim();
  if (callFields.includes(text)) {
    if (!foundFields.includes(text)) {
      foundFields.push(text);
      console.log('  ✅ Found field:', text);
    }
  }
});

if (foundFields.length === 0) {
  console.log('  ❌ No call panel fields found');
}
console.log('');

// Test 6: Final verdict
console.log('═══════════════════════════════════════════════════');
console.log('📊 FINAL RESULTS:');
console.log('═══════════════════════════════════════════════════');

if (transactionIdValue) {
  console.log('✅✅✅ SUCCESS! Transaction ID detected:', transactionIdValue);
  console.log('');
  console.log('👉 The extension SHOULD be able to detect this call!');
  console.log('   If it\'s not working, there may be an iframe issue.');
} else if (foundTransactionIdLabel) {
  console.log('⚠️ PARTIAL SUCCESS!');
  console.log('   • Found "Transaction ID" label: YES');
  console.log('   • Found Transaction ID value: NO');
  console.log('');
  console.log('👉 The label exists but the value couldn\'t be extracted.');
  console.log('   The Transaction ID might be in a different format.');
} else if (fiveDigitNumbers && fiveDigitNumbers.length > 0) {
  console.log('⚠️ POSSIBLE TRANSACTION ID:');
  console.log('   Found 5-digit number(s):', fiveDigitNumbers.join(', '));
  console.log('');
  console.log('👉 One of these might be the Transaction ID,');
  console.log('   but the "Transaction ID" label wasn\'t found.');
} else {
  console.log('❌ DETECTION FAILED');
  console.log('   • No "Transaction ID" label found');
  console.log('   • No 5-digit numbers found');
  console.log('   • Call panel fields found:', foundFields.length);
  console.log('');
  console.log('👉 POSSIBLE CAUSES:');
  console.log('   1. You might be in the wrong frame (main vs iframe)');
  console.log('   2. No active call currently');
  console.log('   3. Transaction ID is in a different format');
  console.log('');
  console.log('💡 TRY THIS:');
  console.log('   1. Make sure you have an ACTIVE call');
  console.log('   2. Make sure Transaction ID is VISIBLE on screen');
  console.log('   3. Try running this script in different frames:');
  console.log('      • In Console, at the top left, click the dropdown');
  console.log('      • Select "control_frame" or "crm_frame"');
  console.log('      • Run this script again');
}

console.log('═══════════════════════════════════════════════════');
