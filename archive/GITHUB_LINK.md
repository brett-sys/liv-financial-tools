# Link this project to GitHub

You created a repo on GitHub. To connect this folder and push your code:

1. **Get your repo URL**  
   Open your repo on GitHub → click the green **Code** button → copy the **HTTPS** URL (e.g. `https://github.com/YourUsername/YourRepo.git`).

2. **In Terminal, run** (paste your URL in place of the example):
   ```bash
   cd /Users/dunham/Desktop/python
   ./link-to-github.sh "https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
   ```

3. If it asks for **password**, use a **Personal Access Token**, not your GitHub password:  
   GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Generate new token** → check **repo** → generate → copy the token and paste it when Terminal asks for password.

**If you get "git: command not found"**  
Run `xcode-select --install` in Terminal and install the Command Line Tools, then run the script again.
