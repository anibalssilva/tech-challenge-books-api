#!/bin/bash

# Script de inicialização para o Render

echo "Starting Books API..."

# Executar o servidor uvicorn
uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-10000}
