"""
Riguel Cuaderno de Campo Astronomico - Root orchestrator
Starts both backend (uvicorn) and frontend (vite) dev servers.
"""
import subprocess
import sys
import os
import signal
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).parent / "backend"
FRONTEND_DIR = Path(__file__).parent / "frontend"


def start_backend():
    """Start the FastAPI backend server."""
    print("[run.py] Starting backend on http://localhost:8000 ...")
    return subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=BACKEND_DIR,
    )


def start_frontend():
    """Start the Vite frontend dev server."""
    print("[run.py] Starting frontend on http://localhost:5173 ...")
    return subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True,
    )


def main():
    backend_proc = None
    frontend_proc = None

    def shutdown(signum, frame):
        print("\n[run.py] Shutting down...")
        if frontend_proc:
            frontend_proc.terminate()
        if backend_proc:
            backend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        backend_proc = start_backend()
        time.sleep(2)  # Give backend a head start
        frontend_proc = start_frontend()

        print("\n" + "=" * 50)
        print("  Riguel Cuaderno de Campo Astronomico")
        print("  Backend:  http://localhost:8000")
        print("  Frontend: http://localhost:5173")
        print("  API Docs: http://localhost:8000/docs")
        print("=" * 50 + "\n")

        # Wait for both processes
        while True:
            backend_ret = backend_proc.poll()
            frontend_ret = frontend_proc.poll()

            if backend_ret is not None:
                print(f"[run.py] Backend exited with code {backend_ret}")
                break
            if frontend_ret is not None:
                print(f"[run.py] Frontend exited with code {frontend_ret}")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()