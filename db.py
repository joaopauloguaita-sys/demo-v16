"""
Shim de compatibilidade: db.py na raiz simplesmente reexporta tudo do módulo
oficial database.db. Isso evita duplicação de código e mantém funcionando
qualquer import legado `from db import ...`.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.db import *  # noqa: F401,F403
from database.db import (  # noqa: F401
    get_connection,
    inicializar_banco,
    migrar_banco,
    nome_seguro,
)
