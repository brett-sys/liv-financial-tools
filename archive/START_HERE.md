# Start here

You have a PDF generator app and a GitHub repo. Here are the only two things you might want to do.

---

## 1. Run the PDF app (generate PDFs)

**What you do:** Open the **Terminal** app on your Mac (search “Terminal” in Spotlight with Cmd+Space).

Copy and paste these three lines, then press Enter:

```bash
cd /Users/dunham/Desktop/python
source venv/bin/activate
python pdf_generator.py
```

A window will open. Paste your data in the box, then click **Generate IUL Illustration**, **Policy Submitted**, or **Business Card**. The PDF will be created and open in Chrome.

That’s it for using the app.

**If you see “WeasyPrint could not import some external libraries” or “cannot load library 'libgobject-2.0-0'”:** the app needs extra system libraries. In Terminal run (this takes a minute):

```bash
brew install pango cairo gdk-pixbuf libffi
```

If you don’t have Homebrew, install it first: https://brew.sh (one line there to paste in Terminal). Then run the `brew install` line above.

After that, try again:

```bash
cd /Users/dunham/Desktop/python
source venv/bin/activate
python pdf_generator.py
```

If it still fails, run this before the commands above (use the same Terminal window):

```bash
export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH"
```

(On an Intel Mac, use `/usr/local/lib` instead of `/opt/homebrew/lib`.)

---

## 2. Put your project on GitHub (one-time)

You already created a repo: **https://github.com/brett-sys/Pdf-Generator**

**What you do:** Open **Terminal**, then run:

```bash
cd /Users/dunham/Desktop/python
./link-to-github.sh
```

- If it says **“git: command not found”**: run `xcode-select --install`, wait for the install to finish, then run `./link-to-github.sh` again.
- If it asks for a **password**: you need a “Personal Access Token” from GitHub.
  1. In your browser go to: https://github.com/settings/tokens
  2. Click **“Generate new token (classic)”**
  3. Name it (e.g. “my laptop”), check the **repo** box, click **Generate**
  4. Copy the token (it looks like `ghp_xxxx...`)
  5. When Terminal asks for a password, paste that token (you won’t see it as you paste — that’s normal), then press Enter.

After that, your code will be on GitHub. You don’t need to do this again unless you want to push new changes later.

---

## Summary

- **To use the app:** Terminal → `cd /Users/dunham/Desktop/python` → `source venv/bin/activate` → `python pdf_generator.py`
- **To put code on GitHub:** Terminal → `cd /Users/dunham/Desktop/python` → `./link-to-github.sh` (and use a token as the password if it asks)

If something doesn’t work, say which step (1 or 2) and what message you see, and we can fix it.
