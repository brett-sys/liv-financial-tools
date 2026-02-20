/**
 * Google Apps Script: Save Final Expense Questionnaire submissions to a Google Sheet
 *
 * SETUP:
 * 1. Create a new Google Sheet (or use an existing one). Open it.
 * 2. In the Sheet: Extensions > Apps Script. Paste this entire file. Save.
 * 3. Deploy: Deploy > New deployment > Type: Web app.
 *    - Description: Final Expense Questionnaire
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 4. Click Deploy. Copy the Web app URL (ends in /exec).
 * 5. In final-expense-questionnaire.html, find:
 *      action="YOUR_SCRIPT_URL"
 *    Replace YOUR_SCRIPT_URL with the copied URL.
 * 6. Re-upload or republish your page.
 */

function doPost(e) {
  try {
    var p = e.parameter;
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        'Timestamp',
        'P1 Name', 'P1 DOB', 'P1 Gender', 'P1 Height/Weight',
        'P2 Name', 'P2 DOB', 'P2 Gender', 'P2 Height/Weight',
        'Phone', 'Email', 'City', 'State',
        'Service Type', 'Funeral Home Chosen', 'Funeral Home Name',
        'Has Estimate', 'Estimate Amount', 'Has Plot', 'Wants Viewing',
        'Special Wishes',
        'P1 Tobacco', 'P1 Conditions', 'P1 Medications', 'P1 Hospitalized',
        'P2 Tobacco', 'P2 Conditions', 'P2 Medications', 'P2 Hospitalized',
        'Coverage Amount', 'Monthly Budget', 'Beneficiary', 'Beneficiary Names',
        'Existing Insurance', 'Existing Insurance Details',
        'Priorities', 'Additional Notes', 'Best Time'
      ]);
    }

    var p1Conditions = arrParam(e, 'p1_conditions');
    var p2Conditions = arrParam(e, 'p2_conditions');
    var priorities   = arrParam(e, 'priorities');

    sheet.appendRow([
      p.timestamp || new Date().toISOString(),
      p.p1_name || '', p.p1_dob || '', p.p1_gender || '', p.p1_height_weight || '',
      p.p2_name || '', p.p2_dob || '', p.p2_gender || '', p.p2_height_weight || '',
      p.phone || '', p.email || '', p.city || '', p.state || '',
      p.service_type || '', p.funeral_home_chosen || '', p.funeral_home_name || '',
      p.has_estimate || '', p.estimate_amount || '', p.has_plot || '', p.wants_viewing || '',
      p.special_wishes || '',
      p.p1_tobacco || '', p1Conditions, p.p1_medications || '', p.p1_hospitalized || '',
      p.p2_tobacco || '', p2Conditions, p.p2_medications || '', p.p2_hospitalized || '',
      p.coverage_amount || '', p.monthly_budget || '', p.beneficiary || '', p.beneficiary_names || '',
      p.existing_insurance || '', p.existing_insurance_details || '',
      priorities, p.additional_notes || '', p.best_time || ''
    ]);

    return createThankYouPage();
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/** Checkbox fields send multiple values; collect them into a comma-separated string */
function arrParam(e, key) {
  var vals = e.parameters[key];
  if (!vals) return '';
  return vals.join(', ');
}

function createThankYouPage() {
  var html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Thank you</title>'
    + '<style>body{font-family:system-ui,sans-serif;max-width:520px;margin:3rem auto;padding:1.5rem;text-align:center;background:#FAF0E6;color:#1a1a1a;}'
    + 'h1{color:#1e4d7b;font-size:1.8rem;}p{color:#555;font-size:1.1rem;line-height:1.7;}</style></head>'
    + '<body><h1>Thank You!</h1>'
    + '<p>We received your questionnaire answers and will review them right away.</p>'
    + '<p>One of our team members will be in touch shortly to go over your personalized options.</p>'
    + '<p style="margin-top:1.5rem;font-weight:600;color:#1a1a1a;">God bless you and your family.</p>'
    + '</body></html>';
  return HtmlService.createHtmlOutput(html).setTitle('Thank you');
}
