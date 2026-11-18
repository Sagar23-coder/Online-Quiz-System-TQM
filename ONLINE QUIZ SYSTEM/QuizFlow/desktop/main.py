r"""
QuizFlow Desktop Application Entrypoint.
Automatically detects and launches the backend if it is not already running.
Launch with: python main.py or scripts\start_desktop.bat
"""
import os
import sys
import time
import subprocess
from pathlib import Path

# Add desktop directory to sys.path so 'app' imports resolve cleanly
desktop_dir = Path(__file__).resolve().parent
if str(desktop_dir) not in sys.path:
    sys.path.insert(0, str(desktop_dir))

# Attempt to load .env from desktop directory or project root
try:
    from dotenv import load_dotenv
    env_file = desktop_dir / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
    else:
        root_env = desktop_dir.parent / ".env"
        if root_env.exists():
            load_dotenv(dotenv_path=root_env)
except ImportError:
    # Minimal fallback dotenv reader if python-dotenv is not installed in desktop env
    for cand in [desktop_dir / ".env", desktop_dir.parent / ".env"]:
        if cand.exists():
            with open(cand, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def ensure_backend_running():
    """Ensure the FastAPI backend is running; if not, launch it in the background."""
    import requests

    backend_url = os.getenv("QUIZFLOW_API_URL", "http://127.0.0.1:8000/api/v1")
    is_remote = not any(loc in backend_url.lower() for loc in ("127.0.0.1", "localhost", "0.0.0.0"))
    health_url = backend_url.rstrip("/").replace("/api/v1", "/health")
    if not health_url.endswith("/health"):
        health_url += "/health"

    # Check if backend is already responding
    try:
        res = requests.get(health_url, timeout=3.0)
        if res.status_code == 200:
            print(f"[✓] Connected to QuizFlow backend at: {backend_url}")
            return
    except Exception:
        pass

    if is_remote:
        print(f"[!] Notice: Cloud backend at {backend_url} did not respond to health check.")
        print("[!] The desktop client will still proceed; verify your network connection or server status.")
        return

    # Locate backend root
    project_root = desktop_dir.parent
    backend_dir = project_root / "backend"
    main_py = backend_dir / "app" / "main.py"

    if not main_py.exists():
        print("[!] Backend directory not found at:", backend_dir)
        return

    print("[*] Starting QuizFlow backend server automatically in background...")
    creationflags = 0
    if os.name == "nt":
        # Launch independently without stealing focus
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    try:
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(backend_dir),
            creationflags=creationflags,
        )

        # Wait briefly for server startup
        for _ in range(8):
            time.sleep(0.5)
            try:
                res = requests.get(health_url, timeout=1.0)
                if res.status_code == 200:
                    print("[✓] Backend server is ready at http://127.0.0.1:8000")
                    return
            except Exception:
                pass
    except Exception as e:
        print("[!] Warning: Could not auto-launch backend:", e)


from app.ui.main_window import MainWindow

if __name__ == "__main__":
    ensure_backend_running()
    app = MainWindow()
    app.mainloop()
