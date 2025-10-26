#!/bin/bash

# Script de inicialização para o Dashboard no Render

echo "Starting Books API Dashboard..."

# Criar diretório de logs se não existir
mkdir -p logs

# Criar arquivo de log vazio se não existir
if [ ! -f logs/api.log ]; then
    echo "Creating empty log file..."
    touch logs/api.log
fi

# Executar o Streamlit
streamlit run dashboard/dashboard.py --server.port=${PORT:-10000} --server.address=0.0.0.0
