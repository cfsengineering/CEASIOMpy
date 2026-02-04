#!/usr/bin/env bash
# ollama setup for Linux Users

curl -fsSL https://ollama.com/install.sh | sh

ollama pull phi3
ollama serve

# If needed...

# To restart
# sudo systemctl restart ollama

# To stop
# sudo systemctl stop ollama
