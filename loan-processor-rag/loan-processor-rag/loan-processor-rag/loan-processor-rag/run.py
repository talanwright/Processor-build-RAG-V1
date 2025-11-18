#!/usr/bin/env python3
"""
Loan Processor RAG System Startup Script
"""

import os
import sys
import subprocess

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def start_server():
    """Start the FastAPI server"""
    print("Starting Loan Processor RAG API server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")

    os.chdir('src')
    subprocess.call([sys.executable, "-m", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

if __name__ == "__main__":
    try:
        # Check if requirements are installed
        try:
            import fastapi
            import chromadb
            import sentence_transformers
        except ImportError:
            print("Installing missing requirements...")
            install_requirements()

        start_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)