"""Allow running as: python -m password_vault"""
from password_vault.app import app, init_db, open_browser
import threading

if __name__ == "__main__":
    init_db()
    print("\n  Password Vault is running at: http://localhost:5050\n")
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(port=5050)
