#!/bin/bash
set -e

echo "================================"
echo "Starting Telegram RAG Bot"
echo "================================"

# Start Ollama server in background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
sleep 5

MAX_RETRIES=30
RETRY_COUNT=0
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Ollama failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "Waiting for Ollama... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✓ Ollama is ready!"

# Check if model exists, if not pull it
echo "Checking for model: ${OLLAMA_MODEL:-llama3.2:3b}"
if ! ollama list | grep -q "${OLLAMA_MODEL:-llama3.2:3b}"; then
    echo "Model not found. Downloading ${OLLAMA_MODEL:-llama3.2:3b}..."
    echo "This may take several minutes on first run..."
    ollama pull "${OLLAMA_MODEL:-llama3.2:3b}"
    echo "✓ Model downloaded!"
else
    echo "✓ Model already exists!"
fi

# Start the bot
echo ""
echo "================================"
echo "Starting Telegram Bot"
echo "================================"
python bot_agentic.py

# If bot exits, keep Ollama running for debugging
wait $OLLAMA_PID