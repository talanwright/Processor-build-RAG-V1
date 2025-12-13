#!/bin/bash

# Setup script for Loan Processor RAG System
# This script creates a virtual environment and installs all dependencies

set -e  # Exit on error

echo "=========================================="
echo "Loan Processor RAG System Setup"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
echo "This may take a few minutes..."
echo ""

pip install -r requirements.txt

echo ""
echo "✓ All dependencies installed"
echo ""

# Initialize vector database
echo "=========================================="
echo "Initializing Vector Database"
echo "=========================================="
echo ""

python3 init_database.py

echo ""
echo "=========================================="
echo "SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "To use the system:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run the API server:"
echo "   cd src && python3 run.py"
echo "   OR"
echo "   python3 simple_rag_api.py"
echo ""
echo "3. To deactivate the virtual environment later:"
echo "   deactivate"
echo ""
