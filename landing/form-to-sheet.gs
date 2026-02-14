/**
 * Google Apps Script: Save burial program form submissions to a Google Sheet
 *
 * SETUP:
 * 1. Create a new Google Sheet (or use an existing one). Open it.
 * 2. In the Sheet: Extensions → Apps Script. Paste this entire file. Save.
 *    (This ties the script to that sheet so responses go there.)
 * 3. Deploy: Deploy → New deployment → Type: Web app.
 *    - Description: Burial form handler
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 4. Click Deploy. Copy the Web app URL (ends in /exec).
 * 5. In your landing page index.html, find:
 *    <https://script.google.com/macros/s/AKfycby1j8ZZ_c7tWYqiyIfeej2aJE-Nc5vmLbfHZ95_xSLbZKju4nhOm8U2viZ7ve2jpYYS/exec>
 *    Replace YOUR_SCRIPT_URL with the copied URL (the /exec one).
 * 6. Re-upload or republish your landing page.
 */

function doPost(e) {
  try {
    var params = e.parameter;
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

    // If the sheet is empty, write headers
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        'Timestamp', 'Full Name', 'Phone', 'Email', 'City', 'State', 'Date of Birth',
        'Beneficiary', 'Beneficiary Other', 'Goal', 'Desired Payment'
      ]);
    }

    var beneficiary = params.beneficiary || '';
    if (params.beneficiary === 'Other' && params.beneficiary_other) {
      beneficiary = 'Other: ' + params.beneficiary_other;
    }

    sheet.appendRow([
      params.timestamp || new Date().toISOString(),
      params.full_name || '',
      params.phone || '',
      params.email || '',
      params.city || '',
      params.state || '',
      params.dob || '',
      beneficiary,
      params.beneficiary_other || '',
      params.goal || '',
      params.payment || ''
    ]);

    return createThankYouPage();
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function createThankYouPage() {
  var html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Thank you</title><style>body{font-family:system-ui,sans-serif;max-width:480px;margin:3rem auto;padding:1.5rem;text-align:center;background:#FAF0E6;color:#1a1a1a;}h1{color:#1e4d7b;}p{color:#555;}</style></head><body><h1>Thank you!</h1><p>We received your information and will be in touch soon.</p></body></html>';
  return HtmlService.createHtmlOutput(html).setTitle('Thank you');
}
