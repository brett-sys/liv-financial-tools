/**
 * Apps Script: Add LeadConduit leads from Gmail to Google Sheets
 * 
 * ONLY pulls emails from Andrew Taylor (andrew@fflusa.com)
 * Extracts lead data and maps to your RECRUITMENT_LEADS sheet structure
 * 
 * Setup: 
 * 1. Open your Google Sheet (RECRUITMENT_LEADS)
 * 2. Extensions → Apps Script
 * 3. Paste this script, save
 * 4. Run addContactsFromGmail() once to authorize
 * 5. Add trigger: Triggers → Add → addContactsFromGmail, Time-driven, every 5 min
 */

function addContactsFromGmail() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  // ONLY emails from Andrew Taylor
  const query = 'from:andrew@fflusa.com is:unread';
  const threads = GmailApp.search(query, 0, 20);
  
  threads.forEach(thread => {
    const msg = thread.getMessages()[0];
    const body = msg.getPlainBody() || "";
    const date = msg.getDate();
    
    const data = parseLeadConduitEmail(body);
    if (data) {
      // Match your sheet columns: Received date, First Name, Last Name, Phone, Email,
      // Source, Location, NPN, Status, AGENCY OVERVIEW VIDEO SENT, Appoint date and time, Notes
      const row = [
        Utilities.formatDate(date, Session.getScriptTimeZone(), "M/d/yyyy"),
        data.firstName,
        data.lastName,
        data.phone,
        data.email,
        data.leadSource || "",
        data.postalCode || "",
        data.npn || "",
        data.agentStatus || "",
        "",  // AGENCY OVERVIEW VIDEO SENT (empty)
        "",  // Appoint date and time (empty)
        data.notes || data.productFocus || ""
      ];
      sheet.appendRow(row);
    }
    thread.markRead();
  });
}

function parseLeadConduitEmail(body) {
  const getField = (regex) => {
    const m = body.match(regex);
    return m ? m[1].trim() : "";
  };
  
  const firstName = getField(/(?:\*\*)?First Name(?:\*\*)?:\s*([^\n*]+)/i);
  const lastName = getField(/(?:\*\*)?Last Name(?:\*\*)?:\s*([^\n*]+)/i);
  const email = getField(/(?:\*\*)?Email(?:\*\*)?:\s*([^\s\n]+)/i);
  const phone = getField(/(?:\*\*)?Phone(?:\*\*)?:\s*([^\s\n]+)/i);
  const postalCode = getField(/(?:\*\*)?Postal Code(?:\*\*)?:\s*([^\n*]+)/i);
  const npn = getField(/(?:\*\*)?Agent NPN(?:\s*\(If Available\))?(?:\*\*)?:\s*([^\n*]+)/i);
  const productFocus = getField(/(?:\*\*)?Product Focus(?:\*\*)?:\s*([^\n*]+)/i);
  const notes = getField(/(?:\*\*)?Notes(?:\*\*)?:\s*([^\n*]+)/i);
  const agentStatus = getField(/(?:\*\*)?Agent Status(?:\*\*)?:\s*([^\n*]+)/i);
  const leadSource = getField(/(?:\*\*)?Lead Source(?:\*\*)?:\s*([^\n*]+)/i);
  
  if (!email) return null;
  
  return {
    firstName,
    lastName,
    email,
    phone,
    postalCode,
    npn,
    productFocus,
    notes,
    agentStatus,
    leadSource
  };
}
