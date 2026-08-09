import sys, os
from PIL import Image

from logger_config import get_logger
logger = get_logger(__name__)

# Trava a forma como o Windows relata a escala da tela para o processo,
# ANTES de importar customtkinter. Feito assim, de forma explícita e única,
# em vez de deixar o Windows/customtkinter decidirem sozinhos - isso é o que
# causava a letra abrir maior ou menor dependendo do monitor/momento.
if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 1 = System DPI Aware
    except Exception as e:
        logger.warning("SetProcessDpiAwareness(1) não disponível: %s", e)
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception as e2:
            logger.warning("SetProcessDPIAware também não disponível: %s", e2)

import customtkinter as ctk

# Desativa de vez o "vigia" interno do customtkinter que fica checando a
# escala da tela em segundo plano (o "check_dpi_scaling" que aparecia no
# console) - é ele quem ficava desfazendo a trava de tamanho de fonte depois
# de um tempo, mesmo já tendo travado no início.
try:
    from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker
    ScalingTracker.check_dpi_scaling = classmethod(lambda cls: None)
    ScalingTracker.get_window_scaling = classmethod(lambda cls, *a, **k: 1.0)
    ScalingTracker.get_widget_scaling = classmethod(lambda cls, *a, **k: 1.0)
except Exception as e:
    logger.warning("Não foi possível desativar o scaling automático do customtkinter: %s", e)

from tkinter import messagebox, ttk
import webbrowser
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import inicializar_banco, migrar_banco, get_connection
from tema import aplicar_tema, CORES, fonte, maximizar
import sincronizar
from modules.gerador_bf import gerar_pdf_bf
from auth_utils import gerar_hash_senha, verificar_senha, parece_hash_bcrypt
aplicar_tema()


def _nome_escola_atual():
    """Busca o nome da escola direto do banco (Dados da Escola). Nunca fica
    preso a um texto fixo — muda sozinho se você trocar o cadastro."""
    try:
        conn = get_connection()
        row = conn.execute("SELECT nome_escola FROM dados_escola LIMIT 1").fetchone()
        conn.close()
        if row and row["nome_escola"]:
            return row["nome_escola"]
    except Exception:
        pass
    return "Escola Municipal"



def aplicar_estilo_ttk():
    """
    Configura o estilo das tabelas TTK (Treeview) com as cores da escola.
    Alto contraste: fundo branco, texto azul marinho, cabeçalho azul marinho + texto branco.
    Chamado após a janela principal ser criada.
    """
    from tkinter import ttk
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception as e:
        logger.warning("Tema 'clam' não disponível: %s", e)

    # Cabeçalho das tabelas: azul marinho com texto branco
    style.configure("Treeview.Heading",
                    background="#0a2463",
                    foreground="#ffffff",
                    font=("Segoe UI", 9, "bold"),
                    relief="flat",
                    borderwidth=0)
    style.map("Treeview.Heading",
              background=[("active", "#1e4db7")])

    # Linhas: fundo branco com texto azul marinho
    style.configure("Treeview",
                    background="#ffffff",
                    foreground="#0a2463",
                    fieldbackground="#ffffff",
                    font=("Segoe UI", 9),
                    rowheight=22,
                    borderwidth=0,
                    relief="flat")
    style.map("Treeview",
              background=[("selected", "#1976d2")],
              foreground=[("selected", "#ffffff")])


PERFIS_ADMIN = {"secretaria", "direcao", "pedagoga"}

MENU_ITENS = [
    ("dashboard",        "🏠",  "Dashboard",              None),
    ("sofia_chat",       "🤖",  "Consulte a SofIA",       None),
    ("alunos",           "🎓",  "Alunos",                 None),
    ("professores",      "👨‍🏫", "Professores",            PERFIS_ADMIN),
    ("equipe_apoio",     "🏫",  "Gestão e Equipe",        PERFIS_ADMIN),
    ("---1",             "",    "─────────────────",      None),
    ("turmas",           "🏫",  "Turmas e Horários",      None),
    ("frequencia",       "✅",  "Frequência",             None),
    ("notas",            "📊",  "Notas e Boletins",       None),
    ("disciplinas",      "📚",  "Disciplinas",            None),
    ("tamanhos",         "📏",  "Medidas Individuais",    PERFIS_ADMIN),
    ("---2",             "",    "─────────────────",      None),
    ("calendario",       "📅",  "Calendário Escolar",     None),
    ("central_documentos", "📁", "Central de Documentos", PERFIS_ADMIN),
    ("curso_informatica", "🖥️", "Curso de Informática",  None),
    ("fanfarra",         "🎺", "Fanfarra e Balizas" ,    PERFIS_ADMIN),
    ("xadrez",           "♟️",  "Aula de Xadrez" ,       PERFIS_ADMIN),
    ("---3",             "",    "─────────────────",      PERFIS_ADMIN),
    ("dados_escola",     "🏛",  "Dados da Escola",        PERFIS_ADMIN),
    ("estoque",          "📦",  "Controle de Materiais",  PERFIS_ADMIN),
    ("declaracao_vaga",  "🎟️",  "Declaração/Autorização",   PERFIS_ADMIN),
    ("fila_espera",      "⏳",  "Fila de Espera",         PERFIS_ADMIN),
    ("---4",             "",    "─────────────────",      PERFIS_ADMIN),
    ("config_turmas",    "🏫",  "Config. Turmas Próx. Ano", PERFIS_ADMIN),
    ("vagas",            "🎟️",  "Vagas p/ Próximo Ano",   PERFIS_ADMIN),
    ("matriculas",       "📝",  "Matrículas/Rematrículas", PERFIS_ADMIN),
    ("certificado_conclusao", "📜", "Certificado de Conclusão", PERFIS_ADMIN),
    ("---5",             "",    "─────────────────",      PERFIS_ADMIN),
    ("relatorios",       "📄",  "Relatórios",             PERFIS_ADMIN),
    ("atas",             "📝",  "Atas de Reunião",        PERFIS_ADMIN),
    ("bilhetes",         "🎫",  "Bilhetes - Comunicados", PERFIS_ADMIN),
    ("oficios",          "📩",  "Ofícios",                PERFIS_ADMIN),
    ("email_secretaria", "📧",  "E-mail da Secretaria",   PERFIS_ADMIN),
    ("---6",             "",    "─────────────────",      PERFIS_ADMIN),
    ("patrimonio",       "📦",  "Controle de Patrimônio", PERFIS_ADMIN),
    ("---7",             "",    "─────────────────",      PERFIS_ADMIN),
    ("arq_alunos",       "🗄",  "Arq. Morto — Alunos",   PERFIS_ADMIN),
    ("arq_professores",  "🗄",  "Arq. Morto — Prof.",    PERFIS_ADMIN),
    ("arq_equipe_apoio", "🗄",  "Arq. Morto — Gestão e Equipe", PERFIS_ADMIN),
    ("---8",             "",    "─────────────────",      PERFIS_ADMIN),
    ("galeria",          "🖼️",  "Galeria de Fotos",       None),
    ("usuarios",         "👥",  "Usuários do Sistema",   PERFIS_ADMIN),
    ("base_conhecimento", "🔐", "Base de Conhecimento",  PERFIS_ADMIN),
    ("importacao_sere",  "📥",  "Importar do SERE",       PERFIS_ADMIN),
    ("---9",             "",    "─────────────────",      None),
    ("sobre",            "☎️",  "Contato, Vendas e Suporte", None),
]


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("João - Secretário Escolar — Login")
        self.geometry("440x530")
        self.resizable(False, False)
        self.configure(fg_color=CORES["fundo"])
        aplicar_estilo_ttk()
        self._center()
        self._build_ui()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - 220
        y = (self.winfo_screenheight() // 2) - 265
        self.geometry(f"440x530+{x}+{y}")

    def _build_ui(self):
        card = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=20, width=390, height=470)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # Logo se existir
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image
                img = ctk.CTkImage(Image.open(logo_path), size=(64, 64))
                ctk.CTkLabel(card, image=img, text="").pack(pady=(25, 4))
            except Exception as e:
                logger.warning("Não foi possível carregar o logo na tela de login: %s", e)
                ctk.CTkLabel(card, text="🏫", font=fonte(48)).pack(pady=(25, 4))
        else:
            ctk.CTkLabel(card, text="🏫", font=fonte(48)).pack(pady=(25, 4))

        ctk.CTkLabel(card, text="João - Secretário Escolar", font=fonte(24, "bold"),
                     text_color=CORES["dourado"]).pack()
        ctk.CTkLabel(card, text=_nome_escola_atual(),
                     font=fonte(10), text_color=CORES["subtexto"], wraplength=330).pack(pady=(2, 2))
        ctk.CTkLabel(card, text="Sistema desenvolvido por João Paulo A. Guaita - Licença de uso cedida gratuitamente",
                     font=fonte(10, "bold"), text_color=CORES["acento"]).pack(pady=(0, 22))

        for lbl, attr, show in [("Login", "login_entry", ""), ("Senha", "senha_entry", "•")]:
            ctk.CTkLabel(card, text=lbl, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"], anchor="w").pack(padx=45, fill="x")
            e = ctk.CTkEntry(card, width=300, height=40, show=show)
            e.pack(padx=45, pady=(3, 12))
            setattr(self, attr, e)

        self.login_entry.focus()
        self.senha_entry.bind("<Return>", lambda e: self.fazer_login())

        ctk.CTkButton(card, text="Entrar  →", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      height=44, font=fonte(14, "bold"),
                      command=self.fazer_login, width=300).pack(padx=45)

        self.label_erro = ctk.CTkLabel(card, text="", text_color=CORES["perigo"], font=fonte(12))
        self.label_erro.pack(pady=8)

    def fazer_login(self):
        login = self.login_entry.get().strip()
        senha = self.senha_entry.get().strip()
        if not login or not senha:
            self.label_erro.configure(text="Preencha login e senha.")
            return
        conn = get_connection()
        user = conn.execute(
            "SELECT * FROM usuarios WHERE login=? AND ativo=1 AND (excluido IS NULL OR excluido=0)",
            (login,)).fetchone()
        autenticado = bool(user) and verificar_senha(senha, user["senha"])
        if autenticado and not parece_hash_bcrypt(user["senha"]):
            # Senha antiga em texto puro que bateu com a digitada: migra
            # para hash bcrypt agora, sem exigir nenhuma ação do usuário.
            try:
                novo_hash = gerar_hash_senha(senha)
                conn.execute("UPDATE usuarios SET senha=? WHERE id=?", (novo_hash, user["id"]))
                conn.commit()
            except Exception:
                logger.exception("Falha ao migrar senha para hash do usuário %s", user["login"])
        conn.close()
        if autenticado:
            conn2 = get_connection()
            conn2.execute("INSERT INTO log_acessos (usuario_nome, usuario_login, data_hora, acao) VALUES (?,?,?,'login')",
                          (user["nome"], user["login"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn2.commit()
            conn2.close()
            self.destroy()
            MainApp(dict(user)).mainloop()
        else:
            self.label_erro.configure(text="❌ Usuário ou senha incorretos.")
            self.senha_entry.delete(0, "end")


class MainApp(ctk.CTk):
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.perfil  = usuario.get("perfil", "secretaria")
        self.title(f"João - Secretário Escolar — {usuario['nome']}")
        self.configure(fg_color=CORES["fundo"])
        maximizar(self)
        self._build_ui()
        self.abrir_modulo("dashboard")
        self._relock_scaling()

    def _relock_scaling(self):
        """Força a escala de volta a 1.0 continuamente. É bruto, mas garante
        que a fonte nunca fica grande por mais de 1 segundo, seja qual for
        a causa exata (o customtkinter tem um jeito de mudar isso sozinho
        que não conseguimos neutralizar de outra forma até agora)."""
        try:
            if ScalingTracker.window_scaling != 1.0 or ScalingTracker.widget_scaling != 1.0:
                ctk.set_widget_scaling(1.0)
                ctk.set_window_scaling(1.0)
        except Exception as e:
            logger.debug("Erro ao relockar scaling: %s", e)
        self.after(1000, self._relock_scaling)

    def _tem_acesso(self, perfis):
        return perfis is None or self.perfil in perfis

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # SIDEBAR
        sidebar = ctk.CTkFrame(self, fg_color=CORES["sidebar"], width=245, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        logo_f = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_f.pack(fill="x", padx=15, pady=(18, 4))

        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image
                img = ctk.CTkImage(Image.open(logo_path), size=(36, 36))
                ctk.CTkLabel(logo_f, image=img, text="").pack(side="left", padx=(0, 8))
            except Exception as e:
                logger.warning("Não foi possível carregar o logo na sidebar: %s", e)

        ctk.CTkLabel(logo_f, text="🏫 João - Secretário Escolar", font=fonte(16, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", anchor="w")
        ctk.CTkFrame(sidebar, fg_color=CORES["borda"], height=1).pack(fill="x", padx=15, pady=6)
# --- BOTÕES DE AÇÃO RÁPIDA (grade compacta) ---
        grade = ctk.CTkFrame(sidebar, fg_color="transparent")
        grade.pack(fill="x", padx=10, pady=(6, 4))
        for c in range(3):
            grade.grid_columnconfigure(c, weight=1, uniform="botoes")

        LARGURA_BTN = 76
        ALTURA_BTN = 46
        FONTE_BTN = fonte(10, "bold")

        def _botao_grade(texto, cor, cor_hover, comando, linha, coluna, colspan=1):
            b = ctk.CTkButton(grade, text=texto, fg_color=cor, hover_color=cor_hover,
                              text_color=CORES["texto_claro"], font=FONTE_BTN,
                              width=LARGURA_BTN, height=ALTURA_BTN, corner_radius=8,
                              command=comando)
            b.grid(row=linha, column=coluna, columnspan=colspan, padx=3, pady=3,
                   sticky="ew" if colspan == 1 else "")
            return b

        # Linha 1
        self.btn_inspetores = _botao_grade("👁\nInspetores", "#f39c12", "#d68910",
                                            self.sincronizar_supabase, 0, 0)
        self.btn_bf = _botao_grade("📄\nBF", "#2980b9", "#1c638a", self.abrir_janela_bf, 0, 1)
        _botao_grade("📋\nSERE", "#8e44ad", "#8e44ad",
                     lambda: webbrowser.open("https://www.sere.pr.gov.br/sere/"), 0, 2)

        # Linha 2
        URL_LRCO = "https://auth-cs.identidadedigital.pr.gov.br/centralautenticacao/login.html?response_type=code&client_id=f340f1b1f65b6df5b5e3f94d95b11daf&redirect_uri=https%3A%2F%2Fwww.rcomunicipios.pr.gov.br%2Frcdig&scope=&state=1784287321585&urlCert=https://certauth-cs.identidadedigital.pr.gov.br&dnsCidadao=https://cidadao-cs.identidadedigital.pr.gov.br/centralcidadao&loginPadrao=btnCentral&labelCentral=CPF,Login%20Sentinela&modulosDeAutenticacao=btnSentinela,btnCpf,btnCentral&urlLogo=https%3A%2F%2Fwww.registrodeclasse.seed.pr.gov.br%2Frcdig%2Fimages%2Flogo_sistema.png&acesso=2079&tokenFormat=jwt&exibirLinkAutoCadastro=true&exibirLinkRecuperarSenha=true&exibirLinkAutoCadastroCertificado=false&exibirAviso=true&captcha=false"
        URL_PRESENCA = "https://presenca.mec.gov.br/seb/"
        URL_EPROTOCOLO = "https://auth-cs.identidadedigital.pr.gov.br/centralautenticacao/login.html?response_type=code&client_id=9188905e74c28e489b44e954ec0b9bca&redirect_uri=https%3A%2F%2Fwww.eprotocolo.pr.gov.br%2Fspiweb&scope=null&state=1784287466844&urlCert=https://certauth-cs.identidadedigital.pr.gov.br&dnsCidadao=https://cidadao-cs.identidadedigital.pr.gov.br/centralcidadao&loginPadrao=btnCentral&labelCentral=CPF&modulosDeAutenticacao=btnCertificado,btnCpf,btnSanepar,btnCentral&urlLogo=https%3A%2F%2Fwww.eprotocolo.pr.gov.br%2Fspiweb%2Fimages%2Flogo_eprotocolo.png&acesso=2081&tokenFormat=jwt&exibirLinkAutoCadastro=true&exibirLinkRecuperarSenha=true&exibirLinkAutoCadastroCertificado=false&exibirAviso=true&captcha=false"
        _botao_grade("📝\nLRCO", "#16a085", "#138a72", lambda: webbrowser.open(URL_LRCO), 1, 0)
        _botao_grade("✅\nPresença", "#d35400", "#b8480a", lambda: webbrowser.open(URL_PRESENCA), 1, 1)
        _botao_grade("📑\nE-Protoc.", "#2c3e50", "#22303d", lambda: webbrowser.open(URL_EPROTOCOLO), 1, 2)

        # Linha 3 - Sincronizar, centralizado
        self.btn_sync = _botao_grade("🔄 Sincronizar", "#27ae60", "#219150",
                                      self.acao_sincronizar, 2, 1)

        ctk.CTkFrame(sidebar, fg_color=CORES["borda"], height=1).pack(fill="x", padx=15, pady=4)
        # ----------------------------------------
        self.menu_btns = {}
        menu_scr = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        menu_scr.pack(fill="both", expand=True, padx=5)

        for modulo, icon, label, perfis in MENU_ITENS:
            if not self._tem_acesso(perfis):
                continue
            if modulo.startswith("---"):
                ctk.CTkFrame(menu_scr, fg_color=CORES["borda"], height=1).pack(
                    fill="x", padx=10, pady=3)
                continue
            btn = ctk.CTkButton(
                menu_scr, text=f"  {icon}  {label}", anchor="w",
                fg_color="transparent", hover_color=CORES["sidebar_hover"],
                text_color=CORES["texto_claro"], font=fonte(12),
                height=40, corner_radius=8,
                command=lambda m=modulo: self.abrir_modulo(m))
            btn.pack(fill="x", padx=5, pady=1)
            self.menu_btns[modulo] = btn

        ctk.CTkFrame(sidebar, fg_color=CORES["borda"], height=1).pack(
            fill="x", padx=15, pady=4)
        uf = ctk.CTkFrame(sidebar, fg_color="transparent")
        uf.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(uf, text=f"👤 {self.usuario['nome']}", font=fonte(11),
                     text_color=CORES["subtexto"]).pack(anchor="w")
        ctk.CTkLabel(uf, text=self.perfil.capitalize(), font=fonte(10),
                     text_color=CORES["dourado"]).pack(anchor="w")
        ctk.CTkButton(uf, text="Sair", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      height=30, font=fonte(11), command=self.sair, width=80).pack(anchor="w", pady=5)

        # ÁREA PRINCIPAL
        self.main_frame = ctk.CTkFrame(self, fg_color=CORES["fundo"], corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

    # ------------------------------------------------------------------ NAVEGAÇÃO
    def abrir_modulo(self, nome):
        # Re-trava a escala sempre que troca de aba - evita que abrir uma
        # janela (Toplevel), como as de Ofícios/Atas, deixe a fonte gigante
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

        # Registra no histórico de atividades qual aba foi acessada
        try:
            label = next((t[2] for t in MENU_ITENS if t[0] == nome), nome)
            conn_log = get_connection()
            conn_log.execute(
                "INSERT INTO log_acessos (usuario_nome, usuario_login, data_hora, acao) VALUES (?,?,?,?)",
                (self.usuario["nome"], self.usuario["login"],
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"acessou: {label}"))
            conn_log.commit()
            conn_log.close()
        except Exception as e:
            logger.warning("Não foi possível registrar log de acesso: %s", e)

        for m, btn in self.menu_btns.items():
            btn.configure(fg_color=CORES["sidebar_ativo"] if m == nome else "transparent")
        for w in self.main_frame.winfo_children():
            w.destroy()

        so = (self.perfil == "professor")   # professor = somente consulta em módulos pessoais

        if nome == "dashboard":
            self._build_dashboard()
        elif nome == "alunos":
            from modules.alunos import AlunosModule
            AlunosModule(self.main_frame, somente_consulta=so).pack(fill="both", expand=True)
        elif nome == "central_documentos":
            from modules.central_documentos import CentralDocumentosModule
            CentralDocumentosModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "sofia_chat":
            from modules.sofia_chat import SofiaChatModule
            SofiaChatModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "calendario":
            from modules.calendario_escolar import CalendarioEscolarModule
            CalendarioEscolarModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "curso_informatica":
            from modules.curso_informatica import CursoInformaticaModule
            CursoInformaticaModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "fanfarra":
            from modules.fanfarra import FanfarraModule
            FanfarraModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "xadrez":
            from modules.xadrez import XadrezModule
            XadrezModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "tamanhos":
            from modules.registro_tamanhos import RegistroTamanhosModule
            RegistroTamanhosModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "estoque":
            from modules.estoque import EstoqueModule
            EstoqueModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "galeria":
            from modules.galeria import GaleriaModule
            GaleriaModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "professores":
            from modules.professores import ProfessoresModule
            ProfessoresModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "equipe_apoio":
            from modules.equipe_apoio import EquipeApoioModule
            EquipeApoioModule(self.main_frame, somente_consulta=so).pack(fill="both", expand=True)
        elif nome == "turmas":
            from modules.turmas import TurmasModule
            TurmasModule(self.main_frame, somente_consulta=so).pack(fill="both", expand=True)
        elif nome == "disciplinas":
            from modules.disciplinas import DisciplinasModule
            DisciplinasModule(self.main_frame, somente_consulta=so).pack(fill="both", expand=True)
        elif nome == "notas":
            from modules.notas import NotasModule
            NotasModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "frequencia":
            from modules.frequencia import FrequenciaModule
            FrequenciaModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "relatorios":
            from modules.relatorios import RelatoriosModule
            RelatoriosModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "atas":
            from modules.atas import AtasModule
            AtasModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "oficios":
            from modules.oficios import OficiosModule
            OficiosModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "bilhetes":
            from modules.bilhetes import BilhetesModulo
            BilhetesModulo(self.main_frame).pack(fill="both", expand=True)
        elif nome == "email_secretaria":
            from modules.email_secretaria import EmailModule
            EmailModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "dados_escola":
            from modules.dados_escola import DadosEscolaModule
            DadosEscolaModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "importacao_sere":
            from modules.importacao_sere import ImportacaoSereModule
            ImportacaoSereModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "sobre":
            self._tela_sobre()
        elif nome == "certificado_conclusao":
            from modules.certificado_conclusao import CertificadoConclusaoModule
            CertificadoConclusaoModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "patrimonio":
            from modules.patrimonio import PatrimonioModule
            PatrimonioModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "usuarios":
            if self._checar_senha_gestao_usuarios():
                from modules.usuarios import UsuariosModule
                UsuariosModule(self.main_frame).pack(fill="both", expand=True)
            else:
                self.abrir_modulo("dashboard")
        elif nome == "base_conhecimento":
            if self._checar_senha_gestao_usuarios():
                from modules.base_conhecimento import BaseConhecimentoModule
                BaseConhecimentoModule(self.main_frame).pack(fill="both", expand=True)
            else:
                self.abrir_modulo("dashboard")

        # ---- Matrículas / Vagas / Fila de Espera ----
        elif nome == "config_turmas":
            from modules.config_turmas_proximo_ano import ConfigTurmasProximoAnoModule
            ConfigTurmasProximoAnoModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "matriculas":
            from modules.matriculas import MatriculasModule
            MatriculasModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "declaracao_vaga":
            from modules.declaracao_vaga import DeclaracaoVagaModule
            # Re-trava a escala para evitar letras gigantes
            ctk.set_widget_scaling(1.0)
            ctk.set_window_scaling(1.0)
            DeclaracaoVagaModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "vagas":
            from modules.vagas import VagasModule
            VagasModule(self.main_frame).pack(fill="both", expand=True)
        elif nome == "fila_espera":
            from modules.fila_espera import FilaEsperaModule
            FilaEsperaModule(self.main_frame).pack(fill="both", expand=True)

        # ---- Arquivo Morto ----
        elif nome == "arq_alunos":
            self._arq_morto("alunos", "Alunos", "🎓")
        elif nome == "arq_professores":
            self._arq_morto("professores", "Professores", "👨‍🏫")
        elif nome == "arq_equipe_apoio":
            self._arq_morto_equipe()
    def _checar_senha_gestao_usuarios(self):
        conn = get_connection()
        row = conn.execute("SELECT gestao_usuarios_login, gestao_usuarios_senha FROM dados_escola LIMIT 1").fetchone()
        login_certo = (row["gestao_usuarios_login"] if row and row["gestao_usuarios_login"] else "Admin")
        senha_salva = (row["gestao_usuarios_senha"] if row and row["gestao_usuarios_senha"] else None)
        senha_certa = senha_salva if senha_salva else "Admin123"
        conn.close()

        resultado = {"ok": False}
        dlg = ctk.CTkToplevel(self)
        dlg.title("Acesso Restrito")
        dlg.geometry("360x380")
        dlg.resizable(False, False)
        dlg.configure(fg_color=CORES["fundo"])
        dlg.grab_set()
        dlg.transient(self)
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - 180
        y = (dlg.winfo_screenheight() // 2) - 190
        dlg.geometry(f"360x380+{x}+{y}")

        ctk.CTkLabel(dlg, text="🔒 Gestão de Usuários", font=fonte(16, "bold"),
                     text_color=CORES["dourado"]).pack(pady=(20, 4))
        ctk.CTkLabel(dlg, text="Área restrita — informe login e senha.", font=fonte(11),
                     text_color=CORES["subtexto"]).pack(pady=(0, 15))

        ctk.CTkLabel(dlg, text="Login", font=fonte(11, "bold"), text_color=CORES["subtexto"],
                     anchor="w").pack(padx=40, fill="x")
        e_login = ctk.CTkEntry(dlg, width=280, height=36)
        e_login.pack(padx=40, pady=(2, 10))

        ctk.CTkLabel(dlg, text="Senha", font=fonte(11, "bold"), text_color=CORES["subtexto"],
                     anchor="w").pack(padx=40, fill="x")
        e_senha = ctk.CTkEntry(dlg, width=280, height=36, show="•")
        e_senha.pack(padx=40, pady=(2, 4))
        e_login.focus()

        lbl_erro = ctk.CTkLabel(dlg, text="", text_color=CORES["perigo"], font=fonte(11))
        lbl_erro.pack(pady=(2, 4))

        def confirmar():
            if e_login.get().strip() == login_certo and verificar_senha(e_senha.get(), senha_certa):
                if not parece_hash_bcrypt(senha_certa):
                    # Migra a senha (padrão ou antiga em texto puro) para hash bcrypt.
                    try:
                        conn3 = get_connection()
                        conn3.execute(
                            "UPDATE dados_escola SET gestao_usuarios_login=?, gestao_usuarios_senha=?",
                            (login_certo, gerar_hash_senha(e_senha.get())))
                        conn3.commit()
                        conn3.close()
                    except Exception:
                        logger.exception("Falha ao migrar senha de gestão de usuários para hash")
                resultado["ok"] = True
                dlg.destroy()
            else:
                lbl_erro.configure(text="Login ou senha incorretos.")

        e_senha.bind("<Return>", lambda ev: confirmar())
        ctk.CTkButton(dlg, text="Entrar", fg_color=CORES["acento"], hover_color=CORES["acento_hover"],
                      text_color=CORES["texto_claro"], font=fonte(13, "bold"),
                      command=confirmar, width=280, height=38).pack(padx=40, pady=6)

        self.wait_window(dlg)
        return resultado["ok"]

    def acao_sincronizar(self):
        # Aviso visual de que o sistema está trabalhando
        self.btn_sync.configure(text="⏳ Sincronizando...", state="disabled")
        self.update()
        try:
            import sincronizar
            erros = sincronizar.executar_sincronismo()
            if erros:
                messagebox.showwarning(
                    "Nuvem - Sincronizado com pendências",
                    "Alguns dados não sincronizaram:\n\n" + "\n".join(erros)
                )
            else:
                messagebox.showinfo("Nuvem", "Dados sincronizados com sucesso!")
        except Exception as e:
            messagebox.showerror(
                "Erro de Rede",
                "Não foi possível conectar à nuvem. Verifique sua internet e tente novamente.\n\n"
                f"Detalhes técnicos: {e}"
            )
        finally:
            self.btn_sync.configure(text="🔄 Sincronizar Nuvem", state="normal")

    def abrir_janela_bf(self):
        # 1. Cria a janela e define o tamanho
        janela = ctk.CTkToplevel(self)
        janela.title("Gerador de Relatório BF")
        janela.geometry("450x550")
        janela.configure(fg_color=CORES["fundo"])
        
        # Garante que a janela fique na frente de tudo
        janela.grab_set()
        janela.attributes("-topmost", True)
        
        # 2. Container Principal (Um painel para segurar os botões)
        container = ctk.CTkFrame(janela, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        ctk.CTkLabel(container, text="Boletim de Frequência (16 ao 15)", 
                     font=fonte(16, "bold"), text_color=CORES["sidebar"]).pack(pady=(10, 20))
        
        # --- CAMPO MÊS ---
        ctk.CTkLabel(container, text="1. Selecione o Mês de Referência:", 
                     font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w", padx=30)
        
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        # Pega o mês atual da máquina
        import datetime
        mes_atual = meses[datetime.datetime.now().month - 1]
        mes_var = ctk.StringVar(value=mes_atual)
        
        # Menu de seleção
        menu_mes = ctk.CTkOptionMenu(container, values=meses, variable=mes_var, width=300,
                                     fg_color=CORES["acento"], button_color=CORES["acento_hover"])
        menu_mes.pack(pady=(5, 15))

        # --- CAMPO ANO ---
        ctk.CTkLabel(container, text="2. Digite o Ano:", 
                     font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w", padx=30)
        ano_ent = ctk.CTkEntry(container, width=300)
        ano_ent.insert(0, str(datetime.datetime.now().year))
        ano_ent.pack(pady=(5, 15))

        # --- CAMPO DIRETORA ---
        ctk.CTkLabel(container, text="3. Nome da Diretora (Assinatura):", 
                     font=fonte(12, "bold"), text_color=CORES["subtexto"]).pack(anchor="w", padx=30)
        dir_ent = ctk.CTkEntry(container, width=300)
        conn_dir = get_connection()
        diretora_atual = conn_dir.execute(
            "SELECT nome FROM diretores WHERE ativo=1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn_dir.close()
        dir_ent.insert(0, diretora_atual["nome"] if diretora_atual and diretora_atual["nome"] else "")
        dir_ent.pack(pady=(5, 15))

        # --- FUNÇÃO DO BOTÃO ---
        def gerar():
            m_nome = mes_var.get()
            m_num = meses.index(m_nome) + 1
            a_val = ano_ent.get()
            d_val = dir_ent.get()

            try:
                from modules.gerador_bf import gerar_pdf_bf
                gerar_pdf_bf(m_num, a_val, d_val)
                messagebox.showinfo("Sucesso", f"Boletim de {m_nome} gerado com sucesso!", parent=janela)
                janela.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}", parent=janela)

        # --- BOTÕES FINAIS ---
        btn_gerar = ctk.CTkButton(container, text="🚀 GERAR RELATÓRIO PDF", 
                                  font=fonte(14, "bold"), height=50, width=300,
                                  fg_color="#27ae60", hover_color="#219150", 
                                  command=gerar)
        btn_gerar.pack(pady=(20, 10))

        ctk.CTkButton(container, text="Cancelar", fg_color="#c0392b", width=100, 
                      command=janela.destroy).pack(pady=5)
        
        # Força a janela a se desenhar completamente
        janela.update_idletasks()
    def _arq_morto(self, tabela, titulo, icone):
        from modules.arquivo_morto import ArquivoMortoModule

        # Referência à janela principal (self = MainApp = CTk = janela real)
        janela_principal = self

        def callback(parent, reg_id, reativando=True, on_close=None):
            """Abre a ficha de reativação diretamente como CTkToplevel da janela principal."""
            self._abrir_ficha_reativacao(
                janela_principal=janela_principal,
                tabela=tabela,
                titulo=titulo,
                icone=icone,
                reg_id=reg_id,
                on_close=on_close
            )

        ArquivoMortoModule(
            self.main_frame, tabela, titulo, icone,
            campo_nome="nome", form_callback=callback
        ).pack(fill="both", expand=True)

    def _tela_sobre(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True)

        card = ctk.CTkFrame(frame, fg_color=CORES["card"], corner_radius=16)
        card.pack(padx=60, pady=50, fill="both", expand=True)

        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
            img = ctk.CTkImage(Image.open(logo_path), size=(110, 110))
            ctk.CTkLabel(card, image=img, text="").pack(pady=(40, 10))
        except Exception:
            ctk.CTkLabel(card, text="🏫", font=fonte(60)).pack(pady=(40, 10))

        ctk.CTkLabel(card, text=_nome_escola_atual(), font=fonte(20, "bold"),
                     text_color=CORES["dourado"]).pack(pady=(0, 4))
        ctk.CTkLabel(card, text="João - Secretário Escolar", font=fonte(16, "bold"),
                     text_color=CORES["subtexto"]).pack(pady=(0, 20))

        ctk.CTkLabel(card,
            text="Sistema de gestão escolar desenvolvido sob medida, cobrindo cadastro de\n"
                 "alunos e equipe, turmas e horários, notas e frequência, documentos oficiais,\n"
                 "controle de materiais e patrimônio, comunicação com a comunidade escolar e\n"
                 "muito mais — feito para facilitar o dia a dia da secretaria.",
            font=fonte(12), text_color=CORES["texto"], justify="center").pack(pady=(0, 25))

        ctk.CTkLabel(card, text="☎️ Contato, Vendas e Suporte", font=fonte(13, "bold"),
                     text_color=CORES["dourado"]).pack(pady=(5, 8))
        ctk.CTkLabel(card, text="✉  joao.secretarioescolar@gmail.com", font=fonte(12),
                     text_color=CORES["texto"]).pack(pady=2)
        ctk.CTkLabel(card, text="📱  (43) 99908-9871   •   (43) 99936-1415", font=fonte(12),
                     text_color=CORES["texto"]).pack(pady=(2, 25))

        ctk.CTkLabel(card, text="Desenvolvido por João Paulo A. Guaita  •  Licença de uso cedida gratuitamente",
                     font=fonte(11), text_color=CORES["subtexto"]).pack(pady=(0, 30))

    def _arq_morto_equipe(self):
        from modules.arquivo_morto_equipe import ArquivoMortoEquipeModule

        janela_principal = self
        tabelas = [
            ("diretores", "Diretores(as)", "🏛"),
            ("pedagogas", "Pedagogas", "📘"),
            ("secretarios", "Secretário(a)", "🗂️"),
            ("funcionarios", "Funcionários", "🧑‍💼"),
        ]

        def on_reativar(tabela, titulo, icone, reg_id):
            self._abrir_ficha_reativacao(
                janela_principal=janela_principal,
                tabela=tabela, titulo=titulo, icone=icone,
                reg_id=reg_id, on_close=None
            )

        ArquivoMortoEquipeModule(
            self.main_frame, tabelas, on_reativar
        ).pack(fill="both", expand=True)

    def _abrir_ficha_reativacao(self, janela_principal, tabela, titulo,
                                 icone, reg_id, on_close=None):
        """
        Abre a ficha de cadastro para reativação usando a janela principal
        como pai do CTkToplevel — evita o erro 'no attribute tk'.
        """
        from database.db import get_connection, nome_seguro
        from tema import (CORES, fonte, maximizar, abrir_link, vincular_mascara,
                          mascara_cpf, mascara_cep, mascara_telefone, mascara_data,
                          mascara_nis, mascara_portaria, data_bd_para_tela,
                          data_tela_para_bd, ESTADOS_UF, COR_RACA_OPCOES,
                          ESTADO_CIVIL_OPCOES, SITUACAO_FUNCIONAL_OPCOES)
        import pdf_utils
        from datetime import date

        # ── Buscar dados do registro ──────────────────────────────────────────
        if not nome_seguro(tabela):
            raise ValueError(f"Nome de tabela inválido: {tabela!r}")
        conn = get_connection()
        row = conn.execute(f"SELECT * FROM {tabela} WHERE id=?", (reg_id,)).fetchone()
        conn.close()
        if not row:
            from tkinter import messagebox
            messagebox.showerror("Erro", "Registro não encontrado.")
            return
        dados = dict(row)

        # ── Janela ────────────────────────────────────────────────────────────
        form = ctk.CTkToplevel(janela_principal)
        form.title(f"Reativar Cadastro — {dados.get('nome', '')}")
        maximizar(form)
        form.grab_set()
        form.configure(fg_color=CORES["fundo"])

        # Topo
        topo = ctk.CTkFrame(form, fg_color=CORES["primaria"], corner_radius=0, height=60)
        topo.pack(fill="x", side="top")
        ctk.CTkLabel(topo, text=_nome_escola_atual(),
                     font=fonte(15, "bold"), text_color=CORES["dourado"]).pack(
                     side="left", padx=20, pady=15)
        ctk.CTkLabel(topo, text=f"{icone} {titulo}", font=fonte(13),
                     text_color=CORES["texto_claro"]).pack(side="right", padx=20)

        # Faixa de aviso
        faixa = ctk.CTkFrame(form, fg_color=CORES["dourado"], corner_radius=0, height=36)
        faixa.pack(fill="x", side="top")
        ctk.CTkLabel(faixa,
                     text="🗄  Cadastro no Arquivo Morto — revise os dados e clique em "
                          "✅ Reativar para restaurar.",
                     font=fonte(12, "bold"), text_color=CORES["sidebar"]).pack(pady=7)

        scroll = ctk.CTkScrollableFrame(form, fg_color=CORES["fundo"])
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        scroll.columnconfigure((0, 1, 2, 3), weight=1)

        campos = {}

        def secao(txt, row, span=4):
            ctk.CTkLabel(scroll, text=txt, font=fonte(13, "bold"),
                         text_color=CORES["dourado"]).grid(
                row=row, column=0, columnspan=span, sticky="w", padx=10, pady=(16, 2))

        def f(label, key, row, col, w=220, mascara=None, ph=""):
            ctk.CTkLabel(scroll, text=label, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).grid(
                row=row, column=col, sticky="w", padx=8, pady=(5, 0))
            e = ctk.CTkEntry(scroll, width=w, placeholder_text=ph)
            val = dados.get(key, "") or ""
            if "data" in key.lower() and val:
                val = data_bd_para_tela(val)
            e.insert(0, val)
            e.grid(row=row + 1, column=col, padx=8, pady=(0, 3), sticky="ew")
            if mascara:
                vincular_mascara(e, mascara)
            campos[key] = e
            return e

        def fopc(label, key, row, col, opcoes, w=220):
            ctk.CTkLabel(scroll, text=label, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).grid(
                row=row, column=col, sticky="w", padx=8, pady=(5, 0))
            var = ctk.StringVar(value=dados.get(key, "") or (opcoes[0] if opcoes else ""))
            ctk.CTkOptionMenu(scroll, values=opcoes, variable=var, width=w).grid(
                row=row + 1, column=col, padx=8, pady=(0, 3), sticky="ew")
            campos[key] = var
            return var

        # ── Campos (comuns a todas as entidades) ──────────────────────────────
        r = 0
        if tabela == "alunos":
            secao("📋 IDENTIFICAÇÃO", r); r += 1
            f("CGM", "cgm", r, 0, w=140)
            f("Nome Completo *", "nome", r, 1, w=300)
            f("Data de Nascimento", "data_nascimento", r, 2, w=150,
              mascara=mascara_data, ph="DD/MM/AAAA")
            fopc("Sexo", "sexo", r, 3, ["Masculino", "Feminino"], w=140); r += 2
            f("Responsável", "responsavel", r, 0, w=260)
            f("Telefone", "telefone_responsavel", r, 1, w=160, mascara=mascara_telefone)
            f("E-mail", "email", r, 2, w=240); r += 2
            secao("🏫 TURMA", r); r += 1
            conn2 = get_connection()
            turmas = conn2.execute(
                "SELECT id, nome_completo, turno FROM turmas WHERE ativo=1 ORDER BY nome_completo"
            ).fetchall()
            conn2.close()
            t_dict  = {f"{t['nome_completo']} ({t['turno']})": t["id"] for t in turmas}
            t_nomes = ["(Sem turma)"] + list(t_dict.keys())
            turma_atual = "(Sem turma)"
            if dados.get("turma_id"):
                conn2 = get_connection()
                t = conn2.execute("SELECT nome_completo, turno FROM turmas WHERE id=?",
                                  (dados["turma_id"],)).fetchone()
                conn2.close()
                if t: turma_atual = f"{t['nome_completo']} ({t['turno']})"
            turma_var = ctk.StringVar(value=turma_atual)
            ctk.CTkLabel(scroll, text="Turma", font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).grid(row=r, column=0, sticky="w", padx=8, pady=(5, 0))
            ctk.CTkOptionMenu(scroll, values=t_nomes, variable=turma_var, width=280).grid(
                row=r + 1, column=0, padx=8, pady=(0, 3), sticky="ew")
            campos["__turma_var"] = turma_var
            campos["__t_dict"]    = t_dict
            r += 2

        else:
            # Professores, funcionários, pedagogas, secretários, diretores
            secao("👤 IDENTIFICAÇÃO", r); r += 1
            f("Nome Completo *", "nome", r, 0, w=300)
            f("Cargo", "cargo", r, 1, w=220)
            f("CPF", "cpf", r, 2, w=160, mascara=mascara_cpf)
            f("NIS", "nis", r, 3, w=170, mascara=mascara_nis); r += 2
            fopc("Cor/Raça", "cor_raca", r, 0, COR_RACA_OPCOES, w=180)
            fopc("Estado Civil", "estado_civil", r, 1, ESTADO_CIVIL_OPCOES, w=180)
            f("E-mail", "email", r, 2, w=260); r += 2
            secao("📍 ENDEREÇO", r); r += 1
            f("Rua", "rua", r, 0, w=260)
            f("Nº", "numero", r, 1, w=80)
            f("Município", "municipio", r, 2, w=200)
            f("CEP", "cep", r, 3, w=130, mascara=mascara_cep); r += 2
            secao("📞 CONTATO", r); r += 1
            f("Telefone 1", "telefone1", r, 0, w=160, mascara=mascara_telefone)
            f("Telefone 2", "telefone2", r, 1, w=160, mascara=mascara_telefone); r += 2
            secao("💼 SITUAÇÃO FUNCIONAL", r); r += 1
            fopc("Situação", "situacao_funcional", r, 0, SITUACAO_FUNCIONAL_OPCOES, w=180)
            f("Data de Admissão", "data_admissao", r, 1, w=150,
              mascara=mascara_data, ph="DD/MM/AAAA"); r += 2
            if tabela == "diretores":
                secao("📋 NOMEAÇÃO", r); r += 1
                f("Portaria de Nomeação (NNN/AAAA)", "portaria_nomeacao", r, 0,
                  w=200, mascara=mascara_portaria, ph="000/0000"); r += 2

        secao("📁 PASTA DE DOCUMENTOS", r); r += 1
        lf = ctk.CTkFrame(scroll, fg_color="transparent")
        lf.grid(row=r, column=0, columnspan=4, sticky="ew", padx=8, pady=(0, 3))
        link_e = ctk.CTkEntry(lf, width=580, placeholder_text="https://drive.google.com/...")
        link_e.insert(0, dados.get("pasta_documentos", "") or "")
        link_e.pack(side="left", padx=(0, 8))
        campos["pasta_documentos"] = link_e
        ctk.CTkButton(lf, text="📂 Abrir", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      command=lambda: abrir_link(link_e.get()), width=90).pack(side="left")
        r += 1

        secao("📝 OBSERVAÇÕES", r); r += 1
        obs = ctk.CTkTextbox(scroll, height=80)
        obs.insert("1.0", dados.get("observacoes", "") or "")
        obs.grid(row=r, column=0, columnspan=4, padx=8, pady=(0, 20), sticky="ew")
        campos["observacoes"] = obs
        r += 1

        # ── Salvar / Reativar ─────────────────────────────────────────────────
        def reativar():
            from tkinter import messagebox
            nome_val = ""
            for key, wid in campos.items():
                if key == "nome":
                    nome_val = wid.get().strip() if hasattr(wid, "get") else ""

            if not nome_val:
                messagebox.showerror("Erro", "O campo Nome é obrigatório!", parent=form)
                return

            vals = {}
            for key, wid in campos.items():
                if key.startswith("__"):
                    continue
                if isinstance(wid, ctk.StringVar):
                    vals[key] = wid.get()
                elif isinstance(wid, ctk.CTkTextbox):
                    vals[key] = wid.get("1.0", "end-1c")
                else:
                    vals[key] = wid.get()

            # Converter datas
            for dk in ["data_nascimento", "data_admissao", "data_matricula"]:
                if dk in vals:
                    vals[dk] = data_tela_para_bd(vals[dk])

            conn = get_connection()
            try:
                from database.db import nome_seguro
                if not nome_seguro(tabela):
                    raise ValueError(f"Nome de tabela inválido: {tabela!r}")
                if tabela == "alunos":
                    t_var = campos.get("__turma_var")
                    t_dct = campos.get("__t_dict", {})
                    vals["turma_id"] = (t_dct.get(t_var.get()) if t_var else None)

                set_clause = ", ".join([f"{k}=:{k}" for k in vals if k != "turma_id" or tabela == "alunos"])
                set_clause += ", arquivado=0, ativo=1, data_arquivamento=NULL"
                vals["_id"] = reg_id
                conn.execute(f"UPDATE {tabela} SET {set_clause} WHERE id=:_id", vals)
                conn.commit()
                messagebox.showinfo("✅ Reativado",
                                    f"Cadastro de {nome_val} reativado com sucesso!", parent=form)
                form.destroy()
                if on_close:
                    on_close()
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=form)
            finally:
                conn.close()

        # ── Barra de botões ───────────────────────────────────────────────────
        bb = ctk.CTkFrame(form, fg_color=CORES["card"], corner_radius=0, height=58)
        bb.pack(fill="x", side="bottom")

        ctk.CTkButton(bb, text="✖ Fechar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=form.destroy, width=110, height=38).pack(side="right", padx=10, pady=10)
        ctk.CTkButton(bb, text="✅ Reativar Cadastro", fg_color=CORES["acento"],
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                      font=fonte(13, "bold"), command=reativar, width=200, height=38).pack(
                      side="right", padx=8, pady=10)
        ctk.CTkLabel(bb, text="Sistema desenvolvido por João Paulo A. Guaita - Licença de uso cedida gratuitamente",
                     font=fonte(11), text_color=CORES["subtexto"]).pack(side="left", padx=20)

    # ------------------------------------------------------------------ DASHBOARD
    def _build_dashboard(self):
        frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True)

        # Cabeçalho
        bv = ctk.CTkFrame(frame, fg_color=CORES["primaria"], corner_radius=14)
        bv.pack(fill="x", padx=25, pady=(20, 0))

        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image
                img = ctk.CTkImage(Image.open(logo_path), size=(52, 52))
                ctk.CTkLabel(bv, image=img, text="").pack(side="left", padx=(20, 8), pady=15)
            except Exception:
                pass

        txt_f = ctk.CTkFrame(bv, fg_color="transparent")
        txt_f.pack(side="left", pady=15)
        ctk.CTkLabel(txt_f, text=_nome_escola_atual(),
                     font=fonte(16, "bold"), text_color=CORES["dourado"]).pack(anchor="w")
        ctk.CTkLabel(txt_f, text=f"Bem-vindo(a), {self.usuario['nome']}! 👋",
                     font=fonte(13), text_color=CORES["texto_claro"]).pack(anchor="w")
        ctk.CTkLabel(txt_f,
                     text="Sistema desenvolvido por João Paulo A. Guaita - Licença de uso cedida gratuitamente",
                     font=fonte(11), text_color=CORES["texto_claro"]).pack(anchor="w")

        # Estatísticas
        conn = get_connection()
        stats = {
            "alunos":       conn.execute("SELECT COUNT(*) FROM alunos WHERE ativo=1 AND arquivado=0").fetchone()[0],
            "masc":         conn.execute("SELECT COUNT(*) FROM alunos WHERE ativo=1 AND arquivado=0 AND sexo='Masculino'").fetchone()[0],
            "fem":          conn.execute("SELECT COUNT(*) FROM alunos WHERE ativo=1 AND arquivado=0 AND sexo='Feminino'").fetchone()[0],
            "professores":  conn.execute("SELECT COUNT(*) FROM professores WHERE ativo=1 AND arquivado=0").fetchone()[0],
            "funcionarios": conn.execute("SELECT COUNT(*) FROM funcionarios WHERE ativo=1 AND arquivado=0").fetchone()[0],
            "turmas":       conn.execute("SELECT COUNT(*) FROM turmas WHERE ativo=1").fetchone()[0],
            "arq_alunos":   conn.execute("SELECT COUNT(*) FROM alunos WHERE arquivado=1").fetchone()[0],
            "arq_profs":    conn.execute("SELECT COUNT(*) FROM professores WHERE arquivado=1").fetchone()[0],
            "arq_funcs":    conn.execute("SELECT COUNT(*) FROM funcionarios WHERE arquivado=1").fetchone()[0],
        }

        cards_data = [
            ("🎓", "Alunos Ativos",  stats["alunos"],       CORES["acento"]),
            ("♂",  "Meninos",        stats["masc"],          CORES["primaria_clara"]),
            ("♀",  "Meninas",        stats["fem"],           CORES["secundaria"]),
            ("👨‍🏫","Professores",    stats["professores"],   "#7e3af2"),
            ("🧑‍💼","Funcionários",   stats["funcionarios"],  CORES["dourado"]),
            ("🏫", "Turmas Ativas",  stats["turmas"],        CORES["sucesso"]),
        ]

        cards_f = ctk.CTkFrame(frame, fg_color="transparent")
        cards_f.pack(fill="x", padx=20, pady=(15, 0))
        cards_f.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        for i, (icon, label, valor, cor) in enumerate(cards_data):
            card = ctk.CTkFrame(cards_f, fg_color=CORES["card"], corner_radius=14)
            card.grid(row=0, column=i, padx=6, pady=5, sticky="nsew")
            ctk.CTkLabel(card, text=icon, font=fonte(28)).pack(pady=(16, 3))
            # Número centralizado e bem visível
            ctk.CTkLabel(card, text=str(valor), font=fonte(32, "bold"),
                         text_color=cor, justify="center", anchor="center").pack(fill="x", padx=10)
            ctk.CTkLabel(card, text=label, font=fonte(11),
                         text_color=CORES["subtexto"], justify="center",
                         anchor="center").pack(fill="x", padx=10, pady=(2, 16))

        # Arquivo morto
        arq_f = ctk.CTkFrame(frame, fg_color=CORES["card"], corner_radius=14)
        arq_f.pack(fill="x", padx=25, pady=(12, 0))
        ctk.CTkLabel(arq_f, text="🗄 Arquivo Morto", font=fonte(13, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=12)
        for txt, val in [("Alunos", stats["arq_alunos"]),
                         ("Professores", stats["arq_profs"]),
                         ("Funcionários", stats["arq_funcs"])]:
            ctk.CTkLabel(arq_f, text=f"{txt}: {val}", font=fonte(12),
                         text_color=CORES["subtexto"]).pack(side="left", padx=20, pady=12)

        # Turmas com alunos/meninos/meninas
        ctk.CTkLabel(frame, text="🏫 Turmas — Alunos por Sexo",
                     font=fonte(15, "bold"), text_color=CORES["dourado"]
                     ).pack(anchor="w", padx=28, pady=(20, 8))

        turmas_card = ctk.CTkFrame(frame, fg_color=CORES["card"], corner_radius=14)
        turmas_card.pack(fill="x", padx=25, pady=(0, 15))

        turmas_res = conn.execute("""
            SELECT t.nome_completo, t.turno,
                   COUNT(a.id) total,
                   SUM(CASE WHEN a.sexo='Masculino' THEN 1 ELSE 0 END) meninos,
                   SUM(CASE WHEN a.sexo='Feminino'  THEN 1 ELSE 0 END) meninas,
                   p.nome as professor
            FROM turmas t
            LEFT JOIN alunos a ON (a.turma_id=t.id OR a.turma_contraturno_id=t.id) AND a.ativo=1 AND a.arquivado=0
            LEFT JOIN professores p ON t.professor_id=p.id
            WHERE t.ativo=1
            GROUP BY t.id ORDER BY t.nome_completo
        """).fetchall()
        conn.close()

        cols = ("turma", "turno", "total", "meninos", "meninas", "professor")
        tree_t = ttk.Treeview(turmas_card, columns=cols, show="headings",
                               height=min(len(turmas_res), 22))
        for col, (txt, w) in {"turma": ("Turma", 160), "turno": ("Turno", 110),
                               "total": ("Total", 60), "meninos": ("Meninos", 70),
                               "meninas": ("Meninas", 70),
                               "professor": ("Professor", 200)}.items():
            tree_t.heading(col, text=txt, anchor="w")
            tree_t.column(col, width=w, anchor="center" if col not in ("turma","professor") else "w")
        tree_t.tag_configure("turma_row", foreground=CORES["turma_texto"])
        for t in turmas_res:
            tree_t.insert("", "end",
                          values=(t["nome_completo"], t["turno"],
                                  t["total"], t["meninos"] or 0, t["meninas"] or 0,
                                  t["professor"] or "—"),
                          tags=("turma_row",))
        tree_t.pack(padx=10, pady=10, fill="x")

        # Atalhos
        ctk.CTkLabel(frame, text="⚡ Atalhos Rápidos",
                     font=fonte(15, "bold"), text_color=CORES["dourado"]
                     ).pack(anchor="w", padx=28, pady=(10, 8))

        at_f = ctk.CTkFrame(frame, fg_color="transparent")
        at_f.pack(fill="x", padx=20, pady=(0, 25))
        at_f.columnconfigure((0, 1, 2, 3), weight=1)

        atalhos = [
            ("+ Novo Aluno",      CORES["acento"],         "alunos"),
            ("📊 Lançar Notas",   "#7e3af2",               "notas"),
            ("✅ Fazer Chamada",  CORES["sucesso"],         "frequencia"),
            ("📄 Relatórios",     CORES["dourado"],         "relatorios"),
            ("🏫 Turmas",         CORES["secundaria"],      "turmas"),
            ("📚 Disciplinas",    CORES["primaria_clara"],  "disciplinas"),
            ("🏛 Dados da Escola",CORES["borda"],           "dados_escola"),
            ("👥 Usuários",       CORES["perigo"],          "usuarios"),
        ]
        for i, (texto, cor, modulo) in enumerate(atalhos):
            if not self._tem_acesso(
                    None if modulo in ("alunos","notas","frequencia","turmas","disciplinas")
                    else PERFIS_ADMIN):
                continue
            ctk.CTkButton(
                at_f, text=texto, fg_color=cor, height=48,
                font=fonte(12, "bold"), text_color=CORES["texto_claro"],
                command=lambda m=modulo: self.abrir_modulo(m)
            ).grid(row=i // 4, column=i % 4, padx=6, pady=5, sticky="ew")

    # ------------------------------------------------------------------ SAIR
    def sair(self):
        if messagebox.askyesno("Sair", "Deseja sair do sistema?"):
            try:
                conn = get_connection()
                conn.execute("INSERT INTO log_acessos (usuario_nome, usuario_login, data_hora, acao) VALUES (?,?,?,'logout')",
                            (self.usuario["nome"], self.usuario["login"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
            except Exception:
                pass
            self.destroy()
            LoginWindow().mainloop()

    def sincronizar_supabase(self):
        try:
            from tkinter import messagebox
            import requests
            import json
            import sqlite3
            from config import SUPABASE_URL, SUPABASE_KEY, supabase_configurado

            if not supabase_configurado():
                messagebox.showerror("Erro", "Credenciais do Supabase não configuradas (verifique o arquivo .env).")
                return

            conn = get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Pega alunos ativos com o nome da turma
            query = """
            SELECT a.*, t.nome_completo as turma_nome
            FROM alunos a
            LEFT JOIN turmas t ON a.turma_id = t.id
            WHERE a.ativo = 1 AND a.arquivado = 0
            """
            alunos = [dict(row) for row in cursor.execute(query).fetchall()]
            conn.close()
            
            # Prepara os dados para o Supabase (remove campos extras que não existem lá)
            dados_para_enviar = []
            for a in alunos:
                d = dict(a)
                # Remove o turma_nome pois ele é gerado pelo JOIN e não existe na tabela alunos do Supabase
                if 'turma_nome' in d: del d['turma_nome']
                dados_para_enviar.append(d)
            
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            }
            
            # Envia para o Supabase (UPSERT baseado no ID)
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/alunos",
                headers=headers,
                data=json.dumps(dados_para_enviar),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                messagebox.showinfo("Sucesso", f"{len(alunos)} alunos sincronizados com a Portaria!")
            else:
                messagebox.showerror("Erro na Sincronização", f"Status: {response.status_code}\n{response.text}")

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            messagebox.showerror("Erro de Rede", "Não foi possível conectar à internet/nuvem. Verifique sua conexão e tente novamente.")
        except Exception as e:
            messagebox.showerror("Erro Fatal", str(e))


if __name__ == "__main__":
    inicializar_banco()
    migrar_banco()
    LoginWindow().mainloop()
