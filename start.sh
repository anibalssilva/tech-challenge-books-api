#!/bin/bash

# Script de inicialização para o Render

echo "Starting Books API..."

# Criar diretório de logs se não existir
mkdir -p logs

# Criar arquivo de log vazio se não existir
if [ ! -f logs/api.log ]; then
    echo "Creating empty log file..."
    touch logs/api.log
fi

# Executar o servidor uvicorn
uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-10000}
