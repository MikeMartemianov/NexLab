"""NexLab AI Code Editor — Native Desktop Launcher.

Usage:
  1. Dev mode:  python desktop_app/app.py
  2. After building the frontend (npm run build in desktop_app/frontend),
     the app serves the static dist/ folder.
  3. Package as .exe:  pyinstaller desktop_app/nexlab.spec
"""

import threading
import time
import sys
import os
import webbrowser
import urllib.request
import urllib.error

# ═══════════ PATH RESOLUTION ═══════════
def _get_base_dir():
    """Return the base directory for bundled data files.
    
    When running from PyInstaller, data is extracted to a temp dir
    accessible via sys._MEIPASS. Otherwise use the script's directory.
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _get_project_root():
    """Return the project root for dev mode, or CWD for exe mode."""
    if getattr(sys, 'frozen', False):
        return os.getcwd()
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


BASE_DIR = _get_base_dir()
PROJECT_ROOT = _get_project_root()

# Ensure importability
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

# Set environment variable so main.py can find the frontend dist
os.environ["NEXLAB_BASE_DIR"] = BASE_DIR
os.environ["NEXLAB_PROJECT_ROOT"] = PROJECT_ROOT

PORT = 8000
DEV_FRONTEND_URL = "http://localhost:5173"  # Vite dev server


def _start_backend():
    import traceback
    try:
        from desktop_app.backend.main import run_server
        run_server(port=PORT)
    except Exception:
        crash_path = os.path.join(os.getcwd(), "nexlab_crash.log")
        with open(crash_path, "w") as f:
            traceback.print_exc(file=f)
        raise


def _wait_for_backend(timeout: int = 15):
    """Block until backend responds to /api/ping (using stdlib only)."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{PORT}/api/ping")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def main():
    # Start the FastAPI backend in a daemon thread
    t = threading.Thread(target=_start_backend, daemon=True)
    t.start()

    if not _wait_for_backend():
        # If running as exe with no console, write error to log file
        err_path = os.path.join(os.getcwd(), "nexlab_error.log")
        crash_path = os.path.join(os.getcwd(), "nexlab_crash.log")
        crash_info = ""
        if os.path.exists(crash_path):
            with open(crash_path, "r") as f:
                crash_info = f.read()
        with open(err_path, "w") as f:
            f.write("Backend failed to start within 15 seconds.\n")
            if crash_info:
                f.write("\nCrash details:\n")
                f.write(crash_info)
        sys.exit(1)

    # ═══════════ FRONTEND RESOLUTION ═══════════
    # In frozen mode, check bundled dist
    dist_check = os.path.join(BASE_DIR, "desktop_app", "frontend", "dist", "index.html")
    # In dev mode, check relative to current script
    if not os.path.exists(dist_check):
        dist_check = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist", "index.html")

    log_path = os.path.join(os.getcwd(), "nexlab_gui.log")
    with open(log_path, "a") as log:
        log.write(f"[{time.ctime()}] Starting NexLab GUI...\n")
        log.write(f"[{time.ctime()}] PROJECT_ROOT: {PROJECT_ROOT}\n")
        log.write(f"[{time.ctime()}] BASE_DIR: {BASE_DIR}\n")
        
        if os.path.exists(dist_check):
            url = f"http://127.0.0.1:{PORT}"
            log.write(f"[{time.ctime()}] Found production build at {dist_check}. Using URL: {url}\n")
        else:
            url = DEV_FRONTEND_URL
            log.write(f"[{time.ctime()}] UI build missing at {dist_check}. Defaulting to Dev Server: {url}\n")
            log.write(f"[{time.ctime()}] NOTE: If the window is blank or shows 404, run 'npm run dev' in desktop_app/frontend or build the UI.\n")

    # Try to use pywebview for a native window
    try:
        import webview
        
        # ═══════════ FALLBACK UI ═══════════
        # If production build is missing AND we are not in DEV mode (no localhost:5173),
        # we can show a simple instruction page.
        if not os.path.exists(dist_check):
            # Try to see if dev server is up
            dev_up = False
            try:
                with urllib.request.urlopen(DEV_FRONTEND_URL, timeout=1) as r:
                    if r.status == 200: dev_up = True
            except: pass
            
            if not dev_up:
                fallback_path = os.path.join(PROJECT_ROOT, "desktop_app", "fallback.html")
                with open(fallback_path, "w", encoding="utf-8") as f:
                    f.write("""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>NexLab - Build Required</title>
                        <style>
                            body { background: #0d1117; color: #e6edf3; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                            .box { background: #161b22; border: 1px solid #30363d; padding: 40px; border-radius: 12px; max-width: 500px; text-align: center; }
                            h1 { color: #7c3aed; margin-top: 0; }
                            code { background: #000; padding: 4px 8px; border-radius: 4px; color: #a78bfa; font-family: monospace; }
                            .btn { display: inline-block; margin-top: 20px; padding: 10px 20px; background: #7c3aed; color: white; text-decoration: none; border-radius: 6px; }
                        </style>
                    </head>
                    <body>
                        <div class="box">
                            <h1>💎 NexLab AI</h1>
                            <p>The production UI assets are missing.</p>
                            <p>Please run the following command in your terminal:</p>
                            <p><code>nexlab build-gui</code></p>
                            <p>Then restart the application.</p>
                            <a href="https://github.com/MikeMartemianov/NexLab" class="btn">View Documentation</a>
                        </div>
                    </body>
                    </html>
                    """)
                url = "file://" + fallback_path.replace("\\", "/")

        webview.create_window(
            "NexLab AI Code Editor",
            url,
            width=1400,
            height=900,
            min_size=(900, 600),
        )
        webview.start()
    except ImportError:
        # Fallback: just open in browser
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
