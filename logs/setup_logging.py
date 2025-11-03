import logging
import logging.handlers
import structlog
import os
import sys
import json
from pathlib import Path
from database_config import DatabaseConnection

class DatabaseLogHandler(logging.Handler):

    def __init__(self, db_connection: DatabaseConnection):
        super().__init__()
        self.db_connection = db_connection
        # Cria a tabela se não existir
        try:
            # Cria a tabela se não existir
            self.db_connection.create_logs_table()
        except Exception as e:
            print(f"CRÍTICO: Não foi possível criar a tabela api_logs no DB. {e}")
            # Continuamos, mas o log no DB não vai funcionar.
    
    def emit(self, record: logging.LogRecord):
        """
        Processa um registro de log e o envia para o banco de dados.
        """
        try:
            # record.getMessage() contém a string JSON formatada pelo structlog
            log_data = json.loads(record.getMessage())
            
            # Mapeia os campos do JSON para os parâmetros da função
            # Use .get() para evitar KeyErrors se o log não for um log de request
            self.db_connection.log_api_call(
                timestamp=log_data.get("timestamp"),
                level=log_data.get("level"),
                message=log_data.get("event"), # 'event' é a mensagem principal no structlog
                event_id=log_data.get("request_id"), # Mapeia 'request_id' do log para 'event_id' do DB
                method=log_data.get("method"),
                client_host=log_data.get("client_host"),
                status_code=log_data.get("status_code"),
                process_time_ms=log_data.get("process_time_ms"),
                path=log_data.get("path")
            )
        except json.JSONDecodeError:
            # Ignora logs que não são JSON (ex: logs de bibliotecas de terceiros)
            pass
        except Exception as e:
            # Nunca deve travar a aplicação por causa de um log
            print(f"❌ Falha ao salvar log no banco de dados: {e}")
            print(f"Log com falha: {record.getMessage()}")
    

def setup_logging(log_path: Path):
    """Setup logging output format and level."""
    try:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Cria o arquivo de log se não existir
        if not log_path.exists():
            log_path.touch()

        # --- Início da Configuração do Banco de Dados ---
        print("Iniciando conexão com DB para logs...")
        db_conn = DatabaseConnection()
        db_handler = DatabaseLogHandler(db_connection=db_conn)
        db_handler.setLevel(logging.INFO)
        # --- Fim da Configuração do Banco de Dados ---

        # Configura o handler de arquivo com flush automático
        # Abre o arquivo sem buffer para garantir escrita imediata (importante para Render)
        file_handler = logging.handlers.WatchedFileHandler(
            log_path, mode='a', encoding='utf-8', delay=False
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        # Configura o handler de stdout (para Render e console)
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(logging.Formatter("%(message)s"))

        # Configura o root logger com ambos os handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.handlers = []
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stdout_handler)
        root_logger.addHandler(db_handler)

        # Configura structlog para usar o stdlib logging
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                # Output as JSON
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        print(f"[OK] Logging initialized successfully at: {log_path.absolute()}")
        print(f"[DEBUG] File exists: {log_path.exists()}")
        print(f"[DEBUG] File is writable: {os.access(log_path, os.W_OK)}")
        print(f"[DEBUG] File size: {log_path.stat().st_size} bytes")

        # Escreve uma linha de teste
        test_logger = structlog.get_logger("setup_test")
        test_logger.info("logging_initialized_test")

    except Exception as e:
        print(f"[ERROR] Failed to initialize logging: {e}")
        print(f"   Log path attempted: {log_path}")
        # Não lançar a exceção, permitir que a API continue rodando
        # mas configurar um handler mínimo para stdout
        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(logging.INFO)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(stdout_handler)
        print("[WARNING] Fallback: Using stdout logging only")