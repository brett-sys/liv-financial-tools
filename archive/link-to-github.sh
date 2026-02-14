#!/bin/bash
# Link this project to your GitHub repo and push (plan: link_local_project_to_github)
# Your repo: https://github.com/brett-sys/Pdf-Generator
# Run: ./link-to-github.sh
# Or with a different URL: ./link-to-github.sh "https://github.com/OTHER/OtherRepo.git"
# If prompted for password, use a Personal Access Token: GitHub → Settings → Developer settings → Personal access tokens.

set -e
cd "$(dirname "$0")"

# Default to your Pdf-Generator repo if no URL given
URL="${1:-https://github.com/brett-sys/Pdf-Generator.git}"
if [[ ! "$URL" =~ \.git$ ]]; then
  URL="${URL%.git}.git"
fi

echo "Repository URL: $URL"
echo ""

if [ ! -d .git ]; then
  echo "Step 3: git init"
  git init
fi

echo "Step 4: git add ."
git add .

echo "Step 5: git commit -m \"Initial commit\""
git commit -m "Initial commit" || true

echo "Step 6: git remote add origin <your URL>"
git remote remove origin 2>/dev/null || true
git remote add origin "$URL"

echo "Step 7: git branch -M main"
git branch -M main

echo "Step 8: git push -u origin main"
echo "(If asked for password, use a Personal Access Token from GitHub Settings → Developer settings → Personal access tokens.)"
git push -u origin main

echo ""
echo "Done. Your project is linked to $URL"
