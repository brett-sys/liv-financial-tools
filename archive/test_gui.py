#!/usr/bin/env python3
"""Simple test to verify tkinter works"""

import sys

print("Testing tkinter import...")
try:
    import tkinter as tk
    print("✓ tkinter imported successfully")
except ImportError as e:
    print(f"✗ Failed to import tkinter: {e}")
    print("\nTry installing python-tk:")
    print("  brew install python-tk")
    sys.exit(1)

print("Creating test window...")
try:
    root = tk.Tk()
    root.title("Tkinter Test")
    root.geometry("400x200")
    
    label = tk.Label(
        root, 
        text="If you see this window, tkinter is working!\n\nClose this window to continue.",
        font=("Arial", 14),
        padx=20,
        pady=20
    )
    label.pack()
    
    button = tk.Button(
        root,
        text="Close",
        command=root.destroy,
        padx=20,
        pady=10
    )
    button.pack(pady=10)
    
    print("✓ Window created, starting main loop...")
    print("  (The window should appear now)")
    root.mainloop()
    print("✓ Test completed successfully!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
