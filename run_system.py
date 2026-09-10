import subprocess
import time
import sys
import os

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root, "backend")
    frontend_dir = os.path.join(root, "frontend")

    print("[*] Installing Python dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=backend_dir)

    print("[*] Launching Digital Twin FastAPI & WebSocket Backend...")
    backend_process = subprocess.Popen([sys.executable, "main.py"], cwd=backend_dir)

    time.sleep(2)

    print("[*] Installing Frontend NPM dependencies...")
    subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)

    print("[*] Launching GCS Visualization Dashboard (Vite)...")
    frontend_process = subprocess.Popen(["npm", "run", "dev"], cwd=frontend_dir, shell=True)

    print("\n[+] AEROTWIN GCS Platform successfully running!")
    print(" -> GCS Dashboard UI: http://localhost:3000")
    print(" -> Backend Telemetry Engine: http://localhost:8000")
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n[*] Shutting down system services...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    main()
