"""
Funcoes de hash e verificacao de senha usando bcrypt.

O EscolaGest guardava as senhas dos usuarios em texto puro no banco.
Este modulo passa a gravar apenas o hash (irreversivel) da senha,
mantendo compatibilidade com senhas antigas em texto puro ja
cadastradas (elas sao verificadas e re-gravadas como hash no primeiro
login com sucesso).

Como usar:
    from auth_utils import gerar_hash_senha, verificar_senha, parece_hash_bcrypt
"""
import bcrypt


def gerar_hash_senha(senha_texto_puro: str) -> str:
    """Gera o hash bcrypt de uma senha em texto puro."""
    senha_bytes = (senha_texto_puro or "").encode("utf-8")
    hash_bytes = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def parece_hash_bcrypt(valor: str) -> bool:
    """Verifica (por formato) se um valor ja e um hash bcrypt."""
    if not valor:
        return False
    return valor.startswith("$2a$") or valor.startswith("$2b$") or valor.startswith("$2y$")


def verificar_senha(senha_texto_puro: str, senha_armazenada: str) -> bool:
    """
    Compara a senha digitada com o valor salvo no banco.

    Suporta os dois formatos, para nao quebrar contas ja existentes:
    - Hash bcrypt (formato novo, seguro)
    - Texto puro (formato antigo, mantido soh para compatibilidade
      ate o usuario logar novamente e o sistema migrar para hash)
    """
    if not senha_armazenada:
        return False
    if parece_hash_bcrypt(senha_armazenada):
        try:
            return bcrypt.checkpw(
                (senha_texto_puro or "").encode("utf-8"),
                senha_armazenada.encode("utf-8"),
            )
        except ValueError:
            return False
    # Compatibilidade com senhas antigas gravadas em texto puro
    return (senha_texto_puro or "") == senha_armazenada
