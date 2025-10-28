import logging
import logging.handlers
import structlog
from pathlib import Path

def setup_logging(log_path: Path):
    """Setup logging output format and level."""
    try:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Cria o arquivo de log se não existir
        if not log_path.exists():
            log_path.touch()

        # Configura o handler de arquivo com flush automático
        # Abre o arquivo sem buffer para garantir escrita imediata (importante para Render)
        file_handler = logging.handlers.WatchedFileHandler(
            log_path, mode='a', encoding='utf-8', delay=False
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        # Configura o handler de stdout (para Render e console)
        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(logging.Formatter("%(message)s"))

        # Configura o root logger com ambos os handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stdout_handler)

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