#!/bin/bash
# Install system libraries so WeasyPrint works on macOS.
# Run once: ./install-weasyprint-deps.sh
# See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation

set -e
cd "$(dirname "$0")"

if ! command -v brew &>/dev/null; then
  echo "Homebrew is not installed. Install it from https://brew.sh"
  echo "Then run this script again."
  exit 1
fi

echo "Installing Pango, Cairo, and related libraries (needed for WeasyPrint)..."
brew install pango cairo gdk-pixbuf libffi

echo ""
echo "Done. Try running the app again:"
echo "  source venv/bin/activate"
echo "  python pdf_generator.py"
echo ""
echo "If you still see a library error, run this before the commands above:"
if [[ $(uname -m) == "arm64" ]]; then
  echo "  export DYLD_FALLBACK_LIBRARY_PATH=\"/opt/homebrew/lib:\$DYLD_FALLBACK_LIBRARY_PATH\""
else
  echo "  export DYLD_FALLBACK_LIBRARY_PATH=\"/usr/local/lib:\$DYLD_FALLBACK_LIBRARY_PATH\""
fi
