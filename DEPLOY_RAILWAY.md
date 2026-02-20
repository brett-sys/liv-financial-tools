# Deploy to Railway — Step by Step

This gets your Call Logger, Lead Manager, and Password Vault running 24/7 on the internet.

---

## 1. Create a Railway Account

1. Go to [railway.app](https://railway.app)
2. Click **Sign Up** — sign in with your **GitHub** account
3. You'll land on your Railway dashboard

---

## 2. Create a New Project

1. Click **New Project**
2. Choose **Deploy from GitHub Repo**
3. Select your **liv-financial-tools** repo (or whatever your repo is called)
4. Railway will detect it's a Python project

---

## 3. Set Up the Call Logger (Service 1)

1. Click the service that was created
2. Go to **Settings** tab
3. Under **Build & Deploy**:
   - Set **Root Directory** to: `call_logger`
   - Set **Start Command** to: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Go to **Variables** tab and add these (click **+ New Variable** for each):

   ```
   CALL_LOG_SHEET_ID = (your Google Sheet ID — from the sheet URL)
   CALL_LOGGER_SECRET_KEY = (make up a random string)
   CALL_LOGGER_PORT = 5055
   ```

5. **Credentials file**: Since `credentials.json` isn't in Git, you need to add it as a variable:
   - Open your `call_logger/credentials.json` file
   - Copy the entire contents
   - Add a variable called `GOOGLE_CREDENTIALS_JSON` and paste the contents as the value
   - (We'll update the code to read from this variable — see step 6)

6. Go to **Settings > Networking** and click **Generate Domain** — this gives you a permanent public URL like `call-logger-production-abc123.up.railway.app`

---

## 4. Set Up the Lead Manager (Service 2)

1. In your project, click **+ New Service** → **GitHub Repo** → same repo
2. Go to **Settings**:
   - **Root Directory**: `lead_manager`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
3. **Variables**:

   ```
   GHL_API_KEY = (your Go High Level API key)
   GHL_LOCATION_ID = (your GHL location ID)
   LEAD_DRIVE_FOLDER_ID = (your Google Drive folder ID)
   LEAD_MANAGER_SECRET_KEY = (make up a random string)
   GOOGLE_CREDENTIALS_JSON = (paste credentials.json contents)
   ```

4. **Generate Domain** in Settings > Networking

---

## 5. Set Up the Password Vault (Service 3)

1. **+ New Service** → **GitHub Repo** → same repo
2. **Settings**:
   - **Root Directory**: `password_vault`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
3. **Variables**: just needs a `SECRET_KEY` (make one up)
4. **Generate Domain**

---

## 6. Push Your Code

Make sure your latest code is pushed to GitHub:

```bash
cd ~/Desktop/python
git add .
git commit -m "add Railway deploy config"
git push
```

Railway auto-deploys every time you push to GitHub.

---

## 7. Credentials File Handling

Since `credentials.json` can't be in Git (it's a secret), we need the apps to read it from an environment variable on Railway. Add this to the TOP of any file that uses credentials (already done for lead_manager):

```python
import os, json

# If running on Railway, credentials come from env variable
creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if creds_json:
    creds_path = Path("/tmp/credentials.json")
    creds_path.write_text(creds_json)
```

I'll update the code to handle this automatically.

---

## What You Get

After deployment, you'll have 3 permanent URLs that never go down:

| App | URL |
|-----|-----|
| Call Logger | `https://your-call-logger.up.railway.app` |
| Lead Manager | `https://your-lead-manager.up.railway.app` |
| Password Vault | `https://your-password-vault.up.railway.app` |

- No more Cloudflare tunnels
- No more restarting
- Links never change
- Works from any device, anywhere

---

## Cost

Railway gives you a $5 free trial. After that, it's usage-based — typically $5-10/month for all 3 apps running 24/7. Way cheaper than any other option.

---

## Updating

Whenever you make changes locally:

```bash
git add .
git commit -m "your change description"
git push
```

Railway automatically picks up the changes and redeploys in about 60 seconds.
