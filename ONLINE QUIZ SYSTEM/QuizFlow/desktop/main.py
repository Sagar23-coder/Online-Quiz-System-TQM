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


def ensure_backend_running():
    """Ensure the FastAPI backend is running; if not, launch it in the background."""
    import requests

    backend_url = os.getenv("QUIZFLOW_API_URL", "http://127.0.0.1:8000/api/v1")
    health_url = backend_url.replace("/api/v1", "/health")

    # Check if backend is already responding
    try:
        res = requests.get(health_url, timeout=1.5)
        if res.status_code == 200:
            print("[✓] Backend is already running.")
            return
    except Exception:
        pass

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
