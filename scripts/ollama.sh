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


# 1) Refresh package lists
sudo apt-get update

# 2) See if Ollama exists in your repos
apt-cache policy ollama
apt-cache search ollama

sudo apt-get install -y ollama
sudo snap install ollama
