"""
EnviroPulse 3D One-Click Launcher
Starts the FastAPI WebSocket server + GPU WebGL Dashboard on http://localhost:8000
"""

import os
import sys
import webbrowser
import threading
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uvicorn

def open_browser():
    time.sleep(1.5)
    print("\n" + "="*70)
    print("[RUNNING] EnviroPulse 3D Multi-Tier Intelligence Server")
    print("Dashboard URL: http://localhost:8000")
    print("WebSocket URL: ws://localhost:8000/ws/environmental-data")
    print("="*70 + "\n")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, app_dir=backend_dir)
