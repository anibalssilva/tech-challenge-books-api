#!/usr/bin/env python3
"""
Script para criar tabelas no PostgreSQL do Render

Como usar:
1. Obtenha a DATABASE_URL no Render (Dashboard > PostgreSQL > Connect > External Database URL)
2. Execute: python create_database_tables.py
3. Cole a DATABASE_URL quando solicitado
"""

import sys

def create_tables():
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 não está instalado!")
        print("\n📦 Instalando psycopg2-binary...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
        import psycopg2
        print("✅ psycopg2-binary instalado com sucesso!\n")

    print("=" * 70)
    print("🗄️  CRIAÇÃO DE TABELAS NO POSTGRESQL (RENDER)")
    print("=" * 70)
    print()
    print("📋 Instruções:")
    print("1. Acesse: https://dashboard.render.com")
    print("2. Clique no seu PostgreSQL Database")
    print("3. Vá em: Info > Connections > External Database URL")
    print("4. Copie a URL (formato: postgresql://user:pass@host/db)")
    print()

    # Solicitar DATABASE_URL
    database_url = input("🔗 Cole a DATABASE_URL aqui: ").strip()

    if not database_url or not database_url.startswith("postgresql://"):
        print("\n❌ URL inválida! Deve começar com 'postgresql://'")
        sys.exit(1)

    print("\n🔄 Conectando ao banco de dados...")

    try:
        # Conectar ao banco
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        print("✅ Conectado com sucesso!")
        print("\n📊 Criando tabela 'api_logs'...")

        # Criar tabela
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                level VARCHAR(50),
                event VARCHAR(100),
                logger VARCHAR(50),
                method VARCHAR(10),
                path VARCHAR(500),
                status_code INTEGER,
                process_time_ms FLOAT,
                client_host VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Criar índices para melhor performance
        print("🔍 Criando índices...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_api_logs_path ON api_logs(path);
            CREATE INDEX IF NOT EXISTS idx_api_logs_status_code ON api_logs(status_code);
        """)

        # Commit
        conn.commit()

        # Verificar tabela criada
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'api_logs'
            ORDER BY ordinal_position;
        """)

        columns = cur.fetchall()

        print("\n✅ Tabela 'api_logs' criada com sucesso!")
        print("\n📋 Estrutura da tabela:")
        print("-" * 50)
        for col_name, col_type in columns:
            print(f"  • {col_name:<20} {col_type}")
        print("-" * 50)

        # Contar registros
        cur.execute("SELECT COUNT(*) FROM api_logs;")
        count = cur.fetchone()[0]
        print(f"\n📊 Total de registros: {count}")

        # Fechar conexão
        cur.close()
        conn.close()

        print("\n🎉 Processo concluído com sucesso!")
        print("\n💡 Próximos passos:")
        print("   1. Configure a variável DATABASE_URL na sua API no Render")
        print("   2. Modifique o código da API para gravar logs no PostgreSQL")
        print("   3. Configure a mesma DATABASE_URL no dashboard")

    except psycopg2.OperationalError as e:
        print(f"\n❌ Erro de conexão: {e}")
        print("\n🔍 Possíveis causas:")
        print("   • URL incorreta")
        print("   • Database não está 'Available' no Render")
        print("   • Firewall bloqueando a conexão")
        print("   • Credenciais expiradas")
        sys.exit(1)

    except psycopg2.ProgrammingError as e:
        print(f"\n❌ Erro de SQL: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_tables()
