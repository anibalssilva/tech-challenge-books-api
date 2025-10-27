#!/usr/bin/env python
"""
Script para testar se os logs estão sendo gerados corretamente.

Uso:
1. Execute a API: uvicorn api.main:app --reload
2. Em outro terminal, execute: python test_logs.py
3. Verifique o arquivo logs/api.log
"""

import requests
import time
import os

API_URL = os.getenv('API_URL', 'http://localhost:8000')

def test_api_and_logs():
    print("🔍 Testando geração de logs na API...")
    print(f"URL da API: {API_URL}")
    print()

    # Teste 1: Health check (não requer autenticação)
    print("1️⃣ Testando endpoint /api/v1/health...")
    try:
        response = requests.get(f"{API_URL}/api/v1/health")
        print(f"   Status: {response.status_code}")
        print(f"   Resposta: {response.json()}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        print("   ⚠️  Certifique-se de que a API está rodando!")
        return

    print()
    time.sleep(1)

    # Teste 2: Tentar acessar endpoint protegido sem token (deve retornar 401)
    print("2️⃣ Testando endpoint protegido sem autenticação...")
    try:
        response = requests.get(f"{API_URL}/api/v1/books")
        print(f"   Status: {response.status_code} (esperado: 401)")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

    print()
    time.sleep(1)

    # Verificar se logs foram gerados
    print("3️⃣ Verificando arquivo de logs...")
    log_file = "logs/api.log"
    if os.path.exists(log_file):
        size = os.path.getsize(log_file)
        print(f"   ✅ Arquivo encontrado: {log_file}")
        print(f"   📊 Tamanho: {size} bytes")

        if size > 0:
            print()
            print("📄 Últimas 5 linhas do log:")
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    print(f"   {line.strip()}")
        else:
            print("   ⚠️  Arquivo está vazio! Os logs não estão sendo gravados.")
    else:
        print(f"   ❌ Arquivo não encontrado: {log_file}")

    print()
    print("✅ Teste concluído!")
    print()
    print("💡 Para visualizar os logs no dashboard:")
    print("   1. Execute: streamlit run dashboard/dashboard.py")
    print("   2. Acesse: http://localhost:8501")

if __name__ == "__main__":
    test_api_and_logs()
