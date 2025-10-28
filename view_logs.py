#!/usr/bin/env python3
"""
Script para visualizar logs de forma amigável
"""
import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path(__file__).parent / 'logs' / 'api.log'

def format_timestamp(iso_timestamp):
    """Formata timestamp ISO para formato legível"""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return iso_timestamp

def view_logs():
    """Exibe logs de forma formatada"""
    if not LOG_FILE.exists():
        print("[ERROR] Arquivo de log nao encontrado!")
        return

    print("=" * 100)
    print("LOGS DA API - Books API".center(100))
    print("=" * 100)
    print()

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        request_count = 0
        for line in f:
            line = line.strip()
            if not line or not line.startswith('{'):
                continue

            try:
                log = json.loads(line)

                # Apenas exibir logs de request_finished
                if log.get('event') == 'request_finished':
                    request_count += 1

                    method = log.get('method', 'N/A')
                    path = log.get('path', 'N/A')
                    status = log.get('status_code', 'N/A')
                    time_ms = log.get('process_time_ms', 'N/A')
                    timestamp = format_timestamp(log.get('timestamp', ''))
                    client = log.get('client_host', 'N/A')

                    # Indicador baseado no status
                    if status < 300:
                        indicator = '[OK]'
                    elif status < 400:
                        indicator = '[REDIRECT]'
                    elif status < 500:
                        indicator = '[CLIENT_ERROR]'
                    else:
                        indicator = '[SERVER_ERROR]'

                    print(f"{indicator:15} [{timestamp}] {method:6} {path:40} -> {status:3} ({time_ms:.2f}ms) - {client}")

            except json.JSONDecodeError:
                continue

    print()
    print("=" * 100)
    print(f"[STATS] Total de requisicoes processadas: {request_count}")
    print("=" * 100)

if __name__ == '__main__':
    view_logs()
