# LIV Financial landing page

Standalone landing page with a **multi-step form** (questions on the page). Submissions are sent to a Google Apps Script that appends rows to a Google Sheet.

## Form on the page

- **Step 1:** Full Name, Phone, Email, City, State, Date of Birth → Next  
- **Step 2:** Beneficiary, Goal, Desired monthly payment → Back / Submit  

Submit sends the data to your Google Sheet via the script below.

## 1. Send form data to a Google Sheet

1. **Create or open a Google Sheet** (e.g. “Burial program leads”). Keep it open.
2. In the sheet menu: **Extensions → Apps Script**.
3. Delete any sample code and **paste the full contents of `form-to-sheet.gs`**. Save (Ctrl+S).
4. **Deploy:** Click **Deploy → New deployment** → click the gear next to “Select type” → **Web app**.
   - Description: e.g. `Burial form`
   - **Execute as:** Me  
   - **Who has access:** Anyone  
5. Click **Deploy**. When prompted, **Authorize** the app (choose your Google account and allow access).
6. Copy the **Web app URL** (ends in `/exec`).

## 2. Point the landing page form to the script

1. Open **`index.html`** in a text editor.
2. Find:  
   `<form id="burial-form" action="YOUR_SCRIPT_URL" method="POST" target="_blank">`
3. Replace **`YOUR_SCRIPT_URL`** with the Web app URL you copied (the one ending in `/exec`).
4. Save.

After that, when someone submits the form, they’ll be sent to a thank-you page and a new row will appear in your sheet.

## 3. Logo (optional)

The page uses `234.png` (included in this folder) for the logo. To use another image, replace it or set the `src` in the `<img>` tag to a different file.

## 4. Host the page

Put the `landing` folder (with your updated `index.html`) on the web so you have a public URL for ads:

- **Netlify:** Go to [app.netlify.com/drop](https://app.netlify.com/drop) and drag the `landing` folder. Use the URL Netlify gives you.
- **GitHub Pages:** Push the contents of `landing` to a repo and turn on Pages in the repo Settings.
- **Your own site:** Upload the contents of `landing` to a subfolder and use that URL.

Use that URL as the destination for your Facebook (or other) ad.
