#!/usr/bin/env python
"""
QPDS Quick Start Script
Starts the QPDS backend server
"""

import os
import sys
import subprocess

def main():
    print("=" * 50)
    print("🎯 QPDS - Quantitative Poker Decision System")
    print("=" * 50)
    print()

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ is required")
        sys.exit(1)

    print(f"✅ Python {sys.version.split()[0]} detected")

    # Check if venv exists
    venv_path = "venv"
    if not os.path.exists(venv_path):
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", venv_path])

    # Determine activation script
    if sys.platform == "win32":
        pip = os.path.join(venv_path, "Scripts", "pip")
        python = os.path.join(venv_path, "Scripts", "python")
    else:
        pip = os.path.join(venv_path, "bin", "pip")
        python = os.path.join(venv_path, "bin", "python")

    if not os.path.exists(pip):
        print("📦 Bootstrapping pip inside virtual environment...")
        subprocess.run([python, "-m", "ensurepip", "--upgrade"], check=True)

    print("🚀 Upgrading pip...")
    subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    # Install requirements
    print("📦 Installing dependencies...")
    subprocess.run([python, "-m", "pip", "install", "-q", "-r", "requirements.txt"], check=True)

    port = os.environ.get("PORT", "5000")
    env = os.environ.copy()
    env["PORT"] = port

    print()
    print("🚀 Starting QPDS Backend...")
    print("=" * 50)
    print(f"API: http://localhost:{port}")
    print(f"Health Check: http://localhost:{port}/health")
    print()
    print("Open frontend/index.html in your browser to use the UI")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    # Start the backend
    try:
        subprocess.run([python, "-m", "backend.api.app"], env=env)
    except KeyboardInterrupt:
        print("\n👋 QPDS stopped")

if __name__ == "__main__":
    main()
