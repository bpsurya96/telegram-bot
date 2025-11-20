#!/bin/bash

# Telegram RAG Bot - Setup Script
# This script automates the setup process

set -e

echo "================================"
echo "Telegram RAG Bot Setup"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if Ollama is installed
echo ""
echo "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"
else
    echo -e "${RED}✗ Ollama is not installed${NC}"
    echo ""
    echo "Please install Ollama first:"
    echo "  macOS/Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  Windows: Download from https://ollama.ai/download"
    echo ""
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
echo ""
if [ -f ".env" ]; then
    echo ".env file already exists"
else
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env and add your TELEGRAM_BOT_TOKEN${NC}"
fi

# Check if Ollama is running
echo ""
echo "Checking if Ollama server is running..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama server is running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama server is not running${NC}"
    echo ""
    echo "Starting Ollama server..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    echo -e "${GREEN}✓ Ollama server started${NC}"
fi

# Pull LLM model
echo ""
echo "Checking for LLM model..."
if ollama list | grep -q "llama3.2:3b"; then
    echo -e "${GREEN}✓ llama3.2:3b model already downloaded${NC}"
else
    echo "Downloading llama3.2:3b model (this may take a few minutes)..."
    ollama pull llama3.2:3b
    echo -e "${GREEN}✓ Model downloaded${NC}"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p chroma_db
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"

# Final instructions
echo ""
echo "================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your TELEGRAM_BOT_TOKEN"
echo "   Get token from: https://t.me/botfather"
echo ""
echo "2. Run the bot:"
echo "   source venv/bin/activate"
echo "   python bot.py"
echo ""
echo "First run will download:"
echo "  • Embedding model (~90MB)"
echo "  • BLIP vision model (~1GB)"
echo ""
echo "For help, see README.md"
echo ""