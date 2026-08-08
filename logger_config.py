"""
Configuracao central de logging do EscolaGest.

Cria um arquivo de log rotativo em logs/escolagest.log, alem de mostrar
mensagens no console. Assim, quando algo der errado, fica registrado
em vez de simplesmente sumir dentro de um "except" silencioso.

Como usar em qualquer arquivo do projeto:
    from logger_config import get_logger
    logger = get_logger(__name__)
    ...
    try:
        ...
    except Exception:
        logger.exception("Erro ao salvar aluno")
"""
import logging
import os
from logging.handlers import RotatingFileHandler

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOG_DIR = os.path.join(_BASE_DIR, "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "escolagest.log")

_configurado = False


def _configurar_raiz():
    global _configurado
    if _configurado:
        return
    os.makedirs(_LOG_DIR, exist_ok=True)

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    raiz = logging.getLogger("escolagest")
    raiz.setLevel(logging.INFO)

    if not raiz.handlers:
        arquivo_handler = RotatingFileHandler(
            _LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        arquivo_handler.setFormatter(formato)
        raiz.addHandler(arquivo_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formato)
        raiz.addHandler(console_handler)

    _configurado = True


def get_logger(nome="escolagest"):
    """Retorna um logger configurado (arquivo + console)."""
    _configurar_raiz()
    if nome and not nome.startswith("escolagest"):
        nome = f"escolagest.{nome}"
    return logging.getLogger(nome)
