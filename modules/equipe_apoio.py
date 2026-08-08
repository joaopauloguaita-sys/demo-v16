"""
Tela composta: agrupa Diretores(as), Pedagogas, Secretário(a) e Funcionários
numa aba só, cada um em seu próprio bloco com cabeçalho colorido — mesmo
comportamento de sempre (duplo clique abre a ficha, Novo/Editar/Arquivar
funcionam igual), só que sem precisar trocar de aba pra ver cada categoria.

Alunos e Professores continuam em telas separadas, como já eram.
"""
import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tema import CORES, fonte
from modules.diretores import DiretoresModule
from modules.pedagogas import PedagogasModule
from modules.secretarios import SecretariosModule
from modules.funcionarios import FuncionariosModule


class EquipeApoioModule(ctk.CTkFrame):
    """Diretores(as) + Pedagogas + Secretário(a) + Funcionários, em blocos empilhados."""

    def __init__(self, parent, somente_consulta=False):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.somente_consulta = somente_consulta
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🏫 Gestão e Equipe", font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # Ordem pedida: Diretores(as) > Pedagogas > Secretário(a) > Funcionários
        blocos = [
            (DiretoresModule, 6),
            (PedagogasModule, 6),
            (SecretariosModule, 6),
            (FuncionariosModule, 10),
        ]
        for ModuloClasse, altura in blocos:
            card = ctk.CTkFrame(scroll, fg_color=CORES["card"], corner_radius=14)
            card.pack(fill="x", pady=(0, 18))
            miolo = ctk.CTkFrame(card, fg_color="transparent")
            miolo.pack(fill="x", padx=15, pady=15)
            ModuloClasse(miolo, somente_consulta=self.somente_consulta,
                         modo_compacto=True, altura_lista=altura).pack(fill="x")
