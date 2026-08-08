"""
Funções e constantes compartilhadas pelas abas de Matrículas/Rematrículas,
Vagas para o Ano Letivo e Fila de Espera.
"""
import os
import sys

import customtkinter as ctk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte

# Ordem oficial de exibição das turmas nas telas de matrícula/vagas
ORDEM_SERIES = ["Infantil 4", "Infantil 5", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano"]

# Vagas padrão por série, conforme regra da SEED
VAGAS_PADRAO = {
    "Infantil 4": 20, "Infantil 5": 20,
    "1º Ano": 25, "2º Ano": 25, "3º Ano": 25,
    "4º Ano": 30, "5º Ano": 30,
}


def serie_da_turma(nome_completo):
    """Extrai a série de um nome de turma. 'Infantil 4 A' -> 'Infantil 4'."""
    partes = nome_completo.rsplit(" ", 1)
    return partes[0] if len(partes) == 2 else nome_completo


def vagas_padrao_para(nome_completo):
    return VAGAS_PADRAO.get(serie_da_turma(nome_completo), 25)


def chave_ordenacao_turma(nome_completo):
    serie = serie_da_turma(nome_completo)
    letra = nome_completo.rsplit(" ", 1)[-1] if " " in nome_completo else ""
    try:
        pos_serie = ORDEM_SERIES.index(serie)
    except ValueError:
        pos_serie = 999
    return (pos_serie, letra)


def listar_turmas_ordenadas(conn):
    turmas = conn.execute(
        "SELECT id, nome_completo, turno FROM turmas_proximo_ano WHERE excluido IS NULL OR excluido = 0"
    ).fetchall()
    return sorted(turmas, key=lambda t: chave_ordenacao_turma(t["nome_completo"]))


# ============================================================
# JANELINHA: escolher série / turma / turno de destino
# ============================================================
def abrir_dialogo_matricula(parent, aluno_id, nome_aluno, on_concluido=None):
    """Abre a janelinha pra escolher pra qual turma o aluno vai ser
    matriculado/rematriculado no próximo ano. Salva em matriculas_proximo_ano
    e chama on_concluido() ao terminar (pra quem chamou navegar pra outra aba)."""
    conn = get_connection()
    turmas = listar_turmas_ordenadas(conn)
    conn.close()

    if not turmas:
        messagebox.showwarning("Atenção", "Nenhuma turma cadastrada ainda.")
        return

    win = ctk.CTkToplevel(parent)
    win.title("Matrícula / Rematrícula")
    win.geometry("400x300")
    win.grab_set()
    win.configure(fg_color=CORES["fundo"])

    topo = ctk.CTkFrame(win, fg_color=CORES["primaria"], corner_radius=0, height=50)
    topo.pack(fill="x")
    ctk.CTkLabel(topo, text="📝 Matrícula / Rematrícula", font=fonte(14, "bold"),
                 text_color=CORES["dourado"]).pack(padx=15, pady=12)

    corpo = ctk.CTkFrame(win, fg_color=CORES["fundo"])
    corpo.pack(fill="both", expand=True, padx=25, pady=15)

    ctk.CTkLabel(corpo, text=nome_aluno, font=fonte(13, "bold"),
                 text_color=CORES["texto"], wraplength=340).pack(anchor="w", pady=(0, 15))

    ctk.CTkLabel(corpo, text="Para qual turma vai no próximo ano letivo?",
                 font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w")

    nomes_turmas = [f"{t['nome_completo']} ({t['turno']})" for t in turmas]
    mapa_turma = {f"{t['nome_completo']} ({t['turno']})": t["id"] for t in turmas}
    turma_var = ctk.StringVar(value=nomes_turmas[0])
    ctk.CTkOptionMenu(corpo, variable=turma_var, values=nomes_turmas, width=340).pack(pady=(8, 20))

    def confirmar():
        turma_id = mapa_turma[turma_var.get()]
        conn2 = get_connection()
        existente = conn2.execute(
            "SELECT id FROM matriculas_proximo_ano WHERE aluno_id=?", (aluno_id,)).fetchone()
        if existente:
            conn2.execute("UPDATE matriculas_proximo_ano SET turma_destino_id=?, excluido=0 WHERE aluno_id=?",
                          (turma_id, aluno_id))
        else:
            conn2.execute(
                "INSERT INTO matriculas_proximo_ano (aluno_id, turma_destino_id, status) VALUES (?,?,'pendente')",
                (aluno_id, turma_id))
        conn2.commit()
        conn2.close()
        win.destroy()
        if on_concluido:
            on_concluido()

    ctk.CTkButton(corpo, text="✅ Enviar para Matrículas/Rematrículas", fg_color=CORES["acento"],
                  hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                  font=fonte(13, "bold"), command=confirmar, width=340, height=40).pack()
