import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseConnection:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._connect()

    def _connect(self):
        """Estabelece conexao com o banco de dados PostgreSQL."""
        try:
            db_name = os.getenv("DB_NAME")
            db_user = os.getenv("DB_USER")
            db_password = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST")
            db_port = os.getenv("DB_PORT", "5432")

            self.conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            self.cursor = self.conn.cursor()
            print("✅ Conexão com o banco de dados estabelecida com sucesso!")
        except psycopg2.Error as e:
            print(f"❌ Erro ao conectar ao banco de dados: {e}")
            self.conn = None
            self.cursor = None
            raise

    def _disconnect(self):
        """Fecha a conexao com o banco de dados."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Conexão com o banco de dados fechada.")
    
    def ensure_connected(self):
        """Garante que a conexão esteja ativa. Tenta reconectar se necessário."""
        if self.conn is None or self.conn.closed:
            print("Conexão perdida ou inexistente. Tentando reconectar...")
            self._connect()
    
    def log_api_call(self, timestamp, level, message, event_id, method, client_host, status_code, process_time_ms, path):
        self.ensure_connected()
        if not self.conn:
            print("Não foi possível salvar o log: conexão com o banco de dados não disponível.")
            return
        
        try:
            query = """
                INSERT INTO api_logs (timestamp, level, message, event_id, method, client_host, status_code, process_time_ms, path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            data = (timestamp, level, message, event_id, method, client_host, status_code, process_time_ms, path)
            self.cursor.execute(query, data)
            self.conn.commit()
        except psycopg2.Error as e:
            print(f"Erro ao inserir log: {e}")
            if self.conn:
                self.conn.rollback()
            if self.conn and self.conn.closed:
                self._disconnect()
            raise
    
    def create_logs_table(self):
        if not self.conn or self.conn.closed:
            self._connect()
        if not self.conn:
            print("Não foi possível criar a tabela api_logs: conexão com o banco de dados não disponível.")
            return
        try:
            """Cria a tabela de api_logs se não existir."""
            query = """
            CREATE TABLE IF NOT EXISTS api_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                level VARCHAR(50),
                message TEXT,
                event_id VARCHAR(100),
                method VARCHAR(10),
                client_host VARCHAR(100),
                status_code INT,
                process_time_ms FLOAT,
                path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );"""

            self.cursor.execute(query)

            # Criar índices para melhor performance
            print("🔍 Criando índices...")
            index = """
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON api_logs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_logs_path ON api_logs(path);
                CREATE INDEX IF NOT EXISTS idx_logs_status_code ON api_logs(status_code);
            """
            self.cursor.execute(index)
            self.conn.commit()
            print("Tabela criada com sucesso!")
        except psycopg2.Error as e:
            print(f"Erro ao criar tabela: {e}")
            self.conn.rollback()
            raise


        