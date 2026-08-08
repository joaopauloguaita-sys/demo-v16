import customtkinter as ctk
from tkinter import messagebox, ttk
import sys, os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import (CORES, fonte, maximizar, abrir_link, abrir_whatsapp, vincular_mascara,
                   mascara_cpf, mascara_cep, mascara_telefone, mascara_certidao,
                   mascara_geo, mascara_data, mascara_cgm,
                   data_bd_para_tela, data_tela_para_bd,
                   ESTADOS_UF, TIPOS_DEFICIENCIA, NECESSIDADES_ESPECIAIS)
from modules.widgets_extras import OcorrenciasWidget, AtestadosWidget
import modules.pdf_utils as pdf_utils

class AlunosModule(ctk.CTkFrame):
    def __init__(self, parent, somente_consulta=False):
        super().__init__(parent, fg_color=CORES["fundo"])
        self.somente_consulta = somente_consulta
        self._build_ui()
        self.carregar_alunos()

    # ──────────────────────────────────────────────────────── LISTA PRINCIPAL
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="🎓 Gestão de Alunos", font=fonte(22, "bold"),
                     text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)

        # Botão WhatsApp rápido — visível para todos os perfis
        ctk.CTkButton(header, text="💬 WhatsApp", fg_color="#25d366",
                      hover_color="#1da851", text_color="#ffffff",
                      font=fonte(12, "bold"),
                      command=self._whatsapp_rapido, width=130).pack(side="right", padx=10, pady=10)

        if not self.somente_consulta:
            bf = ctk.CTkFrame(header, fg_color="transparent")
            bf.pack(side="right", padx=5, pady=10)
            ctk.CTkButton(bf, text="+ Novo Aluno", fg_color=CORES["acento"],
                          hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"],
                          font=fonte(13, "bold"), command=self.abrir_form_novo,
                          width=130).pack(side="left", padx=4)
            ctk.CTkButton(bf, text="✏ Editar", fg_color=CORES["primaria_clara"],
                          text_color=CORES["texto_claro"],
                          command=self.editar_aluno, width=90).pack(side="left", padx=4)
            ctk.CTkButton(bf, text="🗄 Arquivar", fg_color=CORES["dourado"],
                          hover_color=CORES["dourado_hover"], text_color=CORES["sidebar"],
                          font=fonte(12, "bold"),
                          command=self.arquivar_aluno, width=100).pack(side="left", padx=4)

        bf2 = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        bf2.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(bf2, text="🔍", text_color=CORES["subtexto"]).pack(
            side="left", padx=(15, 4), pady=10)
        self.busca_var = ctk.StringVar()
        self.busca_var.trace("w", lambda *a: self.carregar_alunos())
        ctk.CTkEntry(bf2, textvariable=self.busca_var,
                     placeholder_text="Nome, CGM ou responsável...",
                     width=300).pack(side="left", pady=10)
        self.label_total = ctk.CTkLabel(bf2, text="", text_color=CORES["subtexto"])
        self.label_total.pack(side="right", padx=20)

        tf = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        tf.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("cgm", "nome", "turma", "responsavel", "telefone", "sexo")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=20)
        for col, (txt, w) in {"cgm": ("CGM", 110), "nome": ("Nome", 240),
                               "turma": ("Turma", 160), "responsavel": ("Responsável", 180),
                               "telefone": ("Telefone", 130), "sexo": ("Sexo", 80)}.items():
            self.tree.heading(col, text=txt, anchor="w")
            self.tree.column(col, width=w, anchor="w")
        scr = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scr.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scr.pack(side="right", fill="y", pady=5)
        self.tree.bind("<Double-1>", lambda e: self.ver_ficha())

    def carregar_alunos(self, *a):
        for item in self.tree.get_children():
            self.tree.delete(item)
        busca = self.busca_var.get().strip()
        conn = get_connection()
        rows = conn.execute("""
            SELECT a.id, a.cgm, a.nome, t.nome_completo as turma, t.turno,
                   a.responsavel, a.telefone_responsavel, a.sexo
            FROM alunos a LEFT JOIN turmas t ON a.turma_id=t.id
            WHERE a.arquivado=0 AND (a.nome LIKE ? OR a.cgm LIKE ? OR a.responsavel LIKE ?)
            ORDER BY a.nome
        """, [f"%{busca}%"] * 3).fetchall()
        conn.close()
        for r in rows:
            turma_txt = f"{r['turma']} ({r['turno']})" if r["turma"] else "-"
            self.tree.insert("", "end", iid=r["id"],
                             values=(r["cgm"], r["nome"], turma_txt,
                                     r["responsavel"] or "-",
                                     r["telefone_responsavel"] or "-",
                                     r["sexo"] or "-"))
        self.label_total.configure(text=f"Total: {len(rows)} alunos")

    def _sel_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um aluno.")
            return None
        return int(sel[0])

    def abrir_form_novo(self):  self._abrir_form(None)
    def editar_aluno(self):
        aid = self._sel_id()
        if aid: self._abrir_form(aid)
    def ver_ficha(self):
        aid = self._sel_id()
        if aid: self._abrir_form(aid, somente_visualizar=True)

    def arquivar_aluno(self):
        aid = self._sel_id()
        if not aid: return
        if messagebox.askyesno("Confirmar", "Mover este aluno para o Arquivo Morto?"):
            conn = get_connection()
            conn.execute("UPDATE alunos SET arquivado=1,ativo=0,data_arquivamento=? WHERE id=?",
                         (str(date.today()), aid))
            conn.commit(); conn.close()
            self.carregar_alunos()

    def abrir_para_reativar(self, _p, reg_id, reativando=True, on_close=None):
        self._abrir_form(reg_id, somente_visualizar=False, reativando=True, on_close=on_close)

    # ──────────────────────────────────────────────────────── WHATSAPP RÁPIDO
    def _whatsapp_rapido(self):
        aid = self._sel_id()
        if not aid: return
        conn = get_connection()
        aluno = conn.execute(
            "SELECT nome, responsavel, telefone_responsavel, telefone_mae, telefone_pai "
            "FROM alunos WHERE id=?", (aid,)).fetchone()
        conn.close()
        if not aluno: return

        contatos = []
        if aluno["telefone_responsavel"]:
            contatos.append((f"Responsável — {aluno['responsavel'] or 'Responsável'}",
                             aluno["telefone_responsavel"]))
        if aluno["telefone_mae"]:
            contatos.append(("Mãe", aluno["telefone_mae"]))
        if aluno["telefone_pai"]:
            contatos.append(("Pai", aluno["telefone_pai"]))

        if not contatos:
            messagebox.showwarning("Sem telefone",
                f"Nenhum telefone cadastrado para {aluno['nome']}.")
            return
        if len(contatos) == 1:
            abrir_whatsapp(contatos[0][1]); return

        win = ctk.CTkToplevel(self.winfo_toplevel())
        win.title(f"WhatsApp — {aluno['nome']}")
        win.geometry("380x240")
        win.grab_set()
        win.configure(fg_color=CORES["fundo"])
        topo = ctk.CTkFrame(win, fg_color="#25d366", corner_radius=0, height=50)
        topo.pack(fill="x")
        topo.pack_propagate(False)
        ctk.CTkLabel(topo, text=f"💬  {aluno['nome']}",
                     font=fonte(13, "bold"), text_color="#ffffff").pack(padx=15, pady=12)
        frame = ctk.CTkFrame(win, fg_color=CORES["fundo"])
        frame.pack(fill="both", expand=True, padx=20, pady=15)
        ctk.CTkLabel(frame, text="Selecione o contato:",
                     font=fonte(12), text_color=CORES["subtexto"]).pack(pady=(0, 10))
        for descricao, numero in contatos:
            ctk.CTkButton(frame, text=f"💬  {descricao}  —  {numero}",
                          fg_color="#25d366", hover_color="#1da851",
                          text_color="#ffffff", font=fonte(12, "bold"), height=40,
                          command=lambda n=numero: [win.destroy(), abrir_whatsapp(n)]
                          ).pack(fill="x", pady=4)
        ctk.CTkButton(frame, text="Cancelar", fg_color=CORES["perigo"],
                      hover_color=CORES["perigo_hover"], text_color=CORES["texto_claro"],
                      command=win.destroy, width=100).pack(pady=(10, 0))

    # ──────────────────────────────────────────────────────── FORMULÁRIO
    def _abrir_form(self, aluno_id, somente_visualizar=False, reativando=False, on_close=None):
        from modules import pdf_utils
        from modules.requerimentos_seed import salvar_requerimento, gerar_documento_word
        if self.somente_consulta:
            somente_visualizar = True

        form = ctk.CTkToplevel(self.winfo_toplevel())
        form.title("Novo Aluno" if not aluno_id else "Ficha do Aluno")
        maximizar(form)
        form.grab_set()
        form.configure(fg_color=CORES["fundo"])

        conn = get_connection()
        turmas = conn.execute(
            "SELECT id,nome_completo,turno FROM turmas WHERE ativo=1 ORDER BY nome_completo"
        ).fetchall()
        conn.close()
        t_dict  = {f"{t['nome_completo']} ({t['turno']})": t["id"] for t in turmas}
        t_nomes = ["(Sem turma)"] + list(t_dict.keys())

        dados = {}
        if aluno_id:
            conn = get_connection()
            dados = dict(conn.execute("SELECT * FROM alunos WHERE id=?", (aluno_id,)).fetchone() or {})
            conn.close()

        estado = "disabled" if somente_visualizar else "normal"

        # ── Cabeçalho (topo fixo) ─────────────────────────────────────────
        topo = ctk.CTkFrame(form, fg_color=CORES["primaria"], corner_radius=0, height=60)
        topo.pack(fill="x", side="top")
        topo.pack_propagate(False)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image
                img = ctk.CTkImage(Image.open(logo_path), size=(44, 44))
                ctk.CTkLabel(topo, image=img, text="").pack(side="left", padx=(15, 5), pady=8)
            except Exception:
                pass
        ctk.CTkLabel(topo, text="Escola Municipal TRÁ LÁ LÁ",
                     font=fonte(15, "bold"), text_color=CORES["dourado"]
                     ).pack(side="left", padx=10, pady=15)
        ctk.CTkLabel(topo, text="🎓 Ficha do Aluno", font=fonte(13),
                     text_color=CORES["texto_claro"]).pack(side="right", padx=20)

        if reativando:
            faixa = ctk.CTkFrame(form, fg_color=CORES["dourado"], corner_radius=0, height=34)
            faixa.pack(fill="x", side="top")
            faixa.pack_propagate(False)
            ctk.CTkLabel(faixa,
                         text="🗄 Aluno no Arquivo Morto — revise e clique em Salvar para reativar.",
                         font=fonte(12, "bold"), text_color=CORES["sidebar"]).pack(pady=6)

        # ── Barra de botões (bottom fixo) ─────────────────────────────────
        bb = ctk.CTkFrame(form, fg_color=CORES["card"], corner_radius=0, height=58)
        bb.pack(fill="x", side="bottom")
        bb.pack_propagate(False)

        # ── Scroll central ────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(form, fg_color=CORES["fundo"])
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        scroll.columnconfigure((0, 1, 2, 3), weight=1)

        campos = {}
        r = 0
        r = 0

        # ── Funções auxiliares de campo ───────────────────────────────────
        def secao(txt, row):
            ctk.CTkLabel(scroll, text=txt, font=fonte(13, "bold"),
                         text_color=CORES["dourado"]).grid(
                row=row, column=0, columnspan=4, sticky="w", padx=10, pady=(18, 2))

        def f(label, key, row, col, w=200, mascara=None, ph=""):
            ctk.CTkLabel(scroll, text=label, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).grid(
                row=row, column=col, sticky="w", padx=8, pady=(5, 0))
            e = ctk.CTkEntry(scroll, width=w, placeholder_text=ph, state="normal")
            val = dados.get(key, "") or ""
            if "data" in key.lower() and val:
                val = data_bd_para_tela(val)
            e.insert(0, val)
            e.configure(state=estado)
            e.grid(row=row + 1, column=col, padx=8, pady=(0, 3), sticky="ew")
            if mascara and not somente_visualizar:
                vincular_mascara(e, mascara)
            campos[key] = e
            return e

        def fopc(label, key, row, col, opcoes, w=200):
            ctk.CTkLabel(scroll, text=label, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).grid(
                row=row, column=col, sticky="w", padx=8, pady=(5, 0))
            var = ctk.StringVar(value=dados.get(key, "") or (opcoes[0] if opcoes else ""))
            ctk.CTkOptionMenu(scroll, values=opcoes, variable=var, width=w,
                               state=estado).grid(
                row=row + 1, column=col, padx=8, pady=(0, 3), sticky="ew")
            campos[key] = var
            return var

        def f_tel(label, key, row, col, w=180):
            """Campo de telefone com botão WhatsApp ao lado."""
            ctk.CTkLabel(scroll, text=label, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).grid(
                row=row, column=col, sticky="w", padx=8, pady=(5, 0))
            container = ctk.CTkFrame(scroll, fg_color="transparent")
            container.grid(row=row + 1, column=col, padx=8, pady=(0, 3), sticky="ew")
            e = ctk.CTkEntry(container, width=w - 46,
                              placeholder_text="(00) 00000-0000", state="normal")
            val = dados.get(key, "") or ""
            e.insert(0, val)
            e.configure(state=estado)
            e.pack(side="left")
            if not somente_visualizar:
                vincular_mascara(e, mascara_telefone)
            ctk.CTkButton(container, text="💬", width=36, height=28,
                          fg_color="#25d366", hover_color="#1da851",
                          text_color="#ffffff", font=fonte(14),
                          command=lambda entry=e: abrir_whatsapp(entry.get())
                          ).pack(side="left", padx=(4, 0))
            campos[key] = e

        def multichk(label, key, row, opcoes):
            ctk.CTkLabel(scroll, text=label, font=fonte(11, "bold"),
                         text_color=CORES["subtexto"]).grid(
                row=row, column=0, columnspan=4, sticky="w", padx=8, pady=(6, 0))
            cont = ctk.CTkFrame(scroll, fg_color=CORES["card"], width=650)
            cont.grid(row=row + 1, column=0, columnspan=4, padx=8, pady=(0, 4), sticky="w")
            sels = (dados.get(key, "") or "").split("|")
            vars_c = {}
            for i, op in enumerate(opcoes):
                v = ctk.BooleanVar(value=op in sels)
                ctk.CTkCheckBox(cont, text=op, variable=v, font=fonte(11),
                                text_color=CORES["texto"], state=estado,
                                fg_color=CORES["acento"],
                                hover_color=CORES["acento_hover"]
                                ).grid(row=i // 2, column=i % 2,
                                       sticky="w", padx=10, pady=6)
                vars_c[op] = v
            campos[key] = vars_c

        # ── SEÇÃO: DADOS DE SAÚDE ──────────────────────────────────────────
        r += 1
        secao("🏥 DADOS DE SAÚDE", r); r += 1
        
        # Alérgico (Combo + Campo Descrição)
        ctk.CTkLabel(scroll, text="Possui Alergia?", font=fonte(11, "bold"), text_color=CORES["subtexto"]).grid(row=r, column=0, sticky="w", padx=8, pady=(5, 0))
        val_alergico = str(dados.get("alergico", "Não"))
        if val_alergico not in ["Sim", "Não"]: val_alergico = "Não"
        
        var_alergico = ctk.StringVar(value=val_alergico)
        campos["alergico"] = var_alergico
        
        # O campo de descrição deve habilitar apenas se for "Sim"
        ctk.CTkLabel(scroll, text="Descreva a Alergia", font=fonte(11, "bold"), text_color=CORES["subtexto"]).grid(row=r, column=1, columnspan=2, sticky="w", padx=8, pady=(5, 0))
        ent_alergia = ctk.CTkEntry(scroll, placeholder_text="Quais alergias?", state="normal")
        ent_alergia.insert(0, dados.get("alergia_descricao", "") or "")
        ent_alergia.configure(state=estado)
        ent_alergia.grid(row=r+1, column=1, columnspan=2, padx=8, pady=(0, 3), sticky="ew")
        campos["alergia_descricao"] = ent_alergia
        
        def toggle_alergia(v):
            if somente_visualizar: return
            if v == "Sim":
                ent_alergia.configure(state="normal")
            else:
                ent_alergia.delete(0, "end")
                ent_alergia.configure(state="disabled")
        
        menu_alergico = ctk.CTkOptionMenu(scroll, values=["Não", "Sim"], variable=var_alergico, 
                                           command=toggle_alergia, state=estado, width=120)
        menu_alergico.grid(row=r+1, column=0, padx=8, pady=(0, 3), sticky="ew")
        
        # Inicializar estado do campo
        if val_alergico == "Não" and not somente_visualizar:
            ent_alergia.configure(state="disabled")
        
        r += 2

        # ── SEÇÃO: DADOS ESCOLARES ─────────────────────────────────────────
        secao("🏫 DADOS ESCOLARES", r); r += 1

        # Turmas (Regular e Contraturno)
        f_turmas = ctk.CTkFrame(scroll, fg_color="transparent")
        f_turmas.grid(row=r, column=0, columnspan=4, sticky="ew", padx=8, pady=(5, 0))
        ctk.CTkLabel(f_turmas, text="Turma Regular", font=fonte(11, "bold"), text_color=CORES["subtexto"]).pack(side="left", padx=(0, 5))
        turma_atual = ""
        if dados.get("turma_id"):
            conn = get_connection()
            t = conn.execute("SELECT nome_completo, turno FROM turmas WHERE id=?", (dados["turma_id"],)).fetchone()
            conn.close()
            if t: turma_atual = f"{t['nome_completo']} ({t['turno']})"
        turma_contra_atual = "Nenhum"
        if dados.get("turma_contraturno_id"):
            conn = get_connection()
            tc = conn.execute("SELECT nome_completo, turno FROM turmas WHERE id=?", (dados["turma_contraturno_id"],)).fetchone()
            conn.close()
            if tc: turma_contra_atual = f"{tc['nome_completo']} ({tc['turno']})"
        conn = get_connection()
        turmas = conn.execute("SELECT id, nome_completo, turno FROM turmas WHERE ativo=1 AND tipo != 'contraturno' ORDER BY nome_completo").fetchall()
        turmas_contra = conn.execute("SELECT id, nome_completo, turno FROM turmas WHERE ativo=1 AND tipo = 'contraturno' ORDER BY nome_completo").fetchall()
        conn.close()
        self.t_dict = {f"{t['nome_completo']} ({t['turno']})": t["id"] for t in turmas}
        self.t_dict_contra = {"Nenhum": None}
        self.t_dict_contra.update({f"{t['nome_completo']} ({t['turno']})": t["id"] for t in turmas_contra})
        self.turma_var = ctk.StringVar(value=turma_atual or "(Sem turma)")
        ctk.CTkOptionMenu(f_turmas, values=["(Sem turma)"] + list(self.t_dict.keys()), variable=self.turma_var, state=estado, width=220).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_turmas, text="Contraturno", font=fonte(11, "bold"), text_color=CORES["subtexto"]).pack(side="left", padx=(0, 5))
        self.contra_var = ctk.StringVar(value=turma_contra_atual)
        ctk.CTkOptionMenu(f_turmas, values=list(self.t_dict_contra.keys()), variable=self.contra_var, state=estado, width=220).pack(side="left")
        r += 1

        # Autorização de Saída
        f_saida = ctk.CTkFrame(scroll, fg_color="transparent")
        f_saida.grid(row=r, column=0, columnspan=4, sticky="ew", padx=8, pady=(5, 0))
        ctk.CTkLabel(f_saida, text="🛡️ Autorização de Saída", font=fonte(11, "bold"), text_color=CORES["subtexto"]).pack(side="left", padx=(0, 5))
        opcoes_saida = ["Não sai sozinho", "Pode sair sozinho", "Van Escolar"]
        saida_val = dados.get("saida_autorizada", "Não sai sozinho")
        if saida_val not in opcoes_saida: saida_val = "Não sai sozinho"
        self.saida_var = ctk.StringVar(value=saida_val)
        ctk.CTkOptionMenu(f_saida, values=opcoes_saida, variable=self.saida_var, state=estado, width=220).pack(side="left", padx=(0, 20))
        campos["saida_autorizada"] = self.saida_var
        r += 1

        # Link da Pasta (Drive)
        f_drive = ctk.CTkFrame(scroll, fg_color="transparent")
        f_drive.grid(row=r, column=0, columnspan=4, sticky="ew", padx=8, pady=(5, 0))
        ctk.CTkLabel(f_drive, text="📁 Link da Pasta (Drive)", font=fonte(11, "bold"), text_color=CORES["subtexto"]).pack(side="left", padx=(0, 5))
        link_e = ctk.CTkEntry(f_drive, width=500, placeholder_text="https://drive.google.com/...", state="normal")
        link_e.insert(0, dados.get("pasta_documentos", "") or "")
        link_e.configure(state=estado)
        link_e.pack(side="left", padx=(0, 10))
        campos["pasta_documentos"] = link_e
        ctk.CTkButton(f_drive, text="📂 Abrir Pasta", fg_color=CORES["acento"], 
                      hover_color=CORES["acento_hover"], text_color=CORES["texto_claro"], 
                      command=lambda: abrir_link(link_e.get()), width=120).pack(side="left")
        r += 1

        # ── SEÇÃO: IDENTIFICAÇÃO ──────────────────────────────────────────
        secao("📋 IDENTIFICAÇÃO", r); r += 1
        f("CGM (10 dígitos) *", "cgm", r, 0, w=140, mascara=mascara_cgm)
        f("Nome Completo *",     "nome", r, 1, w=300)
        f("Data de Nascimento",  "data_nascimento", r, 2,
          w=150, mascara=mascara_data, ph="DD/MM/AAAA")
        fopc("Sexo", "sexo", r, 3, ["Masculino", "Feminino"], w=140); r += 2
        fopc("Cor/Raça", "cor_raca", r, 0, ["Branca", "Preta", "Parda", "Amarela", "Indígena", "Não Declarada"], w=180); r += 2
        f("CPF",  "cpf", r, 0, w=160, mascara=mascara_cpf)
        f("RG",   "rg",  r, 1, w=150)
        f("Certidão de Nascimento", "certidao_nascimento", r, 2, w=280,
          mascara=mascara_certidao,
          ph="000000 00 00 0000 0 00000 000 0000000-00")
        f("Município de Nascimento", "municipio_nascimento", r, 3, w=200); r += 2
        fopc("UF de Nascimento", "uf_nascimento", r, 0, ESTADOS_UF, w=120); r += 2

        # ── SEÇÃO: FILIAÇÃO E CONTATO ─────────────────────────────────────
        secao("👪 FILIAÇÃO E CONTATO", r); r += 1
        f("Nome da Mãe",  "nome_mae",  r, 0, w=260)
        f("CPF da Mãe",   "cpf_mae",   r, 1, w=160, mascara=mascara_cpf)
        f_tel("📱 Telefone da Mãe", "telefone_mae", r, 2)
        f("Nome do Pai",  "nome_pai",  r, 3, w=260); r += 2
        f("CPF do Pai",   "cpf_pai",   r, 0, w=160, mascara=mascara_cpf)
        f_tel("📱 Telefone do Pai", "telefone_pai", r, 1)
        f("Responsável *", "responsavel", r, 2, w=260)
        f_tel("📱 Tel. Responsável", "telefone_responsavel", r, 3); r += 2
        f("E-mail", "email", r, 0, w=260); r += 2

        # ── SEÇÃO: ENDEREÇO ───────────────────────────────────────────────
        secao("🏠 ENDEREÇO", r); r += 1
        f("Endereço",  "endereco",  r, 0, w=280)
        f("Bairro",    "bairro",    r, 1, w=200)
        f("Cidade",    "cidade",    r, 2, w=200)
        f("CEP",       "cep",       r, 3, w=130, mascara=mascara_cep); r += 2
        f("Tipo Ident. GEO", "tipo_ident_geo", r, 0, w=200,
          ph="Ex: Conta Sanepar/Copel")
        f("Nº Ident. GEO", "numero_ident_geo", r, 1, w=160,
          mascara=mascara_geo); r += 2

        # ── SEÇÃO: SOCIOECONÔMICO ─────────────────────────────────────────
        secao("👨‍👩‍👧‍👦 SOCIOECONÔMICO", r); r += 1
        fopc("Programas Sociais", "participa_programas_sociais", r, 0,
             ["Não", "Sim"], w=130)
        fopc("Pessoas na residência", "qtd_pessoas_residencia", r, 1,
             [str(n) for n in range(0, 16)], w=130); r += 2

        # ── ATESTADOS E OCORRÊNCIAS (só se já existe o aluno) ────────────
        if aluno_id:
            secao("📄 ATESTADOS / DECLARAÇÕES", r); r += 1
            AtestadosWidget(scroll, "alunos", aluno_id,
                            somente_leitura=self.somente_consulta
                            ).grid(row=r, column=0, columnspan=4,
                                   padx=8, pady=(0, 10), sticky="w"); r += 1
            secao("📋 OCORRÊNCIAS", r); r += 1
            OcorrenciasWidget(scroll, "alunos", aluno_id,
                              somente_leitura=self.somente_consulta
                              ).grid(row=r, column=0, columnspan=4,
                                     padx=8, pady=(0, 10), sticky="w"); r += 1

        # ── SEÇÃO: OBSERVAÇÕES ────────────────────────────────────────────
        secao("📝 OBSERVAÇÕES", r); r += 1
        obs = ctk.CTkTextbox(scroll, height=70, width=650, state="normal")
        obs.insert("1.0", dados.get("observacoes", "") or "")
        obs.configure(state=estado)
        obs.grid(row=r, column=0, columnspan=4, padx=8, pady=(0, 10), sticky="w")
        campos["observacoes"] = obs; r += 1

        # ── SEÇÃO: DEFICIÊNCIAS ───────────────────────────────────────────
        secao("♿ TIPO DE DEFICIÊNCIA (múltipla escolha)", r); r += 1
        multichk("", "tipos_deficiencia", r, TIPOS_DEFICIENCIA); r += 2

        secao("🧩 NECESSIDADES / RECURSOS DE ACESSIBILIDADE (múltipla escolha)", r); r += 1
        multichk("", "necessidades_especiais", r, NECESSIDADES_ESPECIAIS); r += 2

        # ── LÓGICA DE SALVAR ──────────────────────────────────────────────
        campos_db = [
            "cgm", "nome", "data_nascimento", "sexo", "cpf", "rg",
            "certidao_nascimento", "municipio_nascimento", "uf_nascimento",
            "nome_mae", "cpf_mae", "telefone_mae",
            "nome_pai", "cpf_pai", "telefone_pai",
            "responsavel", "telefone_responsavel", "email",
            "endereco", "bairro", "cidade", "cep",
            "tipo_ident_geo", "numero_ident_geo",
            "participa_programas_sociais", "qtd_pessoas_residencia",
            "tipos_deficiencia", "necessidades_especiais",
            "turma_id", "turma_contraturno_id", "pasta_documentos", "data_matricula", "observacoes",
            "alergico", "alergia_descricao", "saida_autorizada",
        ]

        def coletar():
            d = {}
            for key, wid in campos.items():
                if isinstance(wid, dict):
                    d[key] = "|".join(op for op, v in wid.items() if v.get())
                elif isinstance(wid, ctk.StringVar):
                    d[key] = wid.get()
                elif isinstance(wid, ctk.CTkTextbox):
                    d[key] = wid.get("1.0", "end-1c")
                else:
                    d[key] = wid.get()
            for k in ["data_nascimento", "data_matricula"]:
                if k in d:
                    d[k] = data_tela_para_bd(d[k])
            return d

        def salvar():
            d = coletar()
            if not d.get("nome", "").strip() or not d.get("cgm", "").strip():
                messagebox.showerror("Erro", "CGM e Nome são obrigatórios!", parent=form)
                return
            d["turma_id"] = self.t_dict.get(self.turma_var.get())
            d["turma_contraturno_id"] = self.t_dict_contra.get(self.contra_var.get())
            try:
                d["qtd_pessoas_residencia"] = int(d.get("qtd_pessoas_residencia") or 0)
            except ValueError:
                d["qtd_pessoas_residencia"] = 0
            from database.db import nome_seguro
            if any(not nome_seguro(k) for k in campos_db):
                invalidas = [k for k in campos_db if not nome_seguro(k)]
                messagebox.showerror("Erro", f"Campos inválidos: {invalidas}", parent=form)
                return
            vals = {k: d.get(k) for k in campos_db}
            conn = get_connection()
            try:
                if aluno_id:
                    sc = ", ".join([f"{k}=:{k}" for k in campos_db])
                    if reativando:
                        sc += ", arquivado=0, ativo=1, data_arquivamento=NULL"
                    vals["_id"] = aluno_id
                    conn.execute(f"UPDATE alunos SET {sc} WHERE id=:_id", vals)
                else:
                    cs = ", ".join(campos_db)
                    ph = ", ".join([f":{k}" for k in campos_db])
                    conn.execute(
                        f"INSERT INTO alunos ({cs},ativo,arquivado) VALUES ({ph},1,0)", vals)
                conn.commit()
                messagebox.showinfo("Sucesso",
                    "Aluno reativado!" if reativando else "Aluno salvo!", parent=form)
                form.destroy()
                self.carregar_alunos()
                if on_close: on_close()
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=form)
            finally:
                conn.close()

        def blocos_pdf():
            d = coletar()
            def_txt = (d.get("tipos_deficiencia", "") or "").replace("|", ", ") or "Nenhuma"
            nec_txt = (d.get("necessidades_especiais", "") or "").replace("|", ", ") or "Nenhuma"
            blocos = [
                ("titulo", "Dados Escolares"),
                ("tabela", [["Campo", "Informação"],
                    ["CGM",    d.get("cgm", "-")],
                    ["Nome",   d.get("nome", "-")],
                    ["Turma",  self.turma_var.get()],
                    ["Data de Matrícula", d.get("data_matricula", "-")]]),
                ("titulo", "Identificação"),
                ("tabela", [["Campo", "Informação"],
                    ["Data de Nascimento", d.get("data_nascimento", "-")],
                    ["Sexo",  d.get("sexo", "-")],
                    ["CPF",   d.get("cpf",  "-")],
                    ["Certidão de Nascimento", d.get("certidao_nascimento", "-")],
                    ["Naturalidade",
                     f"{d.get('municipio_nascimento','-')}/{d.get('uf_nascimento','-')}"]]),
                ("titulo", "Filiação e Contato"),
                ("tabela", [["Campo", "Informação"],
                    ["Mãe",          d.get("nome_mae", "-")],
                    ["CPF Mãe",      d.get("cpf_mae",  "-")],
                    ["Tel. Mãe",     d.get("telefone_mae", "-")],
                    ["Pai",          d.get("nome_pai", "-")],
                    ["CPF Pai",      d.get("cpf_pai",  "-")],
                    ["Responsável",  d.get("responsavel", "-")],
                    ["Tel. Responsável", d.get("telefone_responsavel", "-")]]),
                ("titulo", "Endereço"),
                ("tabela", [["Campo", "Informação"],
                    ["Endereço", d.get("endereco", "-")],
                    ["Bairro",   d.get("bairro",   "-")],
                    ["Cidade",   d.get("cidade",   "-")],
                    ["CEP",      d.get("cep",      "-")]]),
                ("titulo", "Deficiências / Necessidades"),
                ("tabela", [["Tipo de Deficiência", def_txt],
                            ["Necessidades Especiais", nec_txt]]),
            ]

            if aluno_id and messagebox.askyesno("Imprimir Extras", "Deseja incluir Ocorrências e Atestados na impressão?"):
                conn = get_connection()
                ocorr = conn.execute("SELECT data, descricao, registrado_por FROM ocorrencias WHERE entidade='alunos' AND entidade_id=? ORDER BY data DESC", (aluno_id,)).fetchall()
                if ocorr:
                    blocos.append(("titulo", "Histórico de Ocorrências"))
                    linhas_oc = [["Data", "Descrição", "Registrado por"]]
                    for oc in ocorr:
                        linhas_oc.append([data_bd_para_tela(oc["data"]), oc["descricao"], oc["registrado_por"] or "-"] )
                    blocos.append(("tabela", linhas_oc))
                
                atest = conn.execute("SELECT tipo, data, duracao, unidade_duracao, observacao FROM atestados WHERE entidade='alunos' AND entidade_id=? ORDER BY data DESC", (aluno_id,)).fetchall()
                if atest:
                    blocos.append(("titulo", "Atestados / Declarações"))
                    linhas_at = [["Tipo", "Data", "Duração", "Observação"]]
                    for at in atest:
                        linhas_at.append([at["tipo"], data_bd_para_tela(at["data"]), f"{at['duracao']} {at['unidade_duracao']}", at["observacao"] or "-"])
                    blocos.append(("tabela", linhas_at))
                conn.close()

            return blocos

        def pdf_acao():
            pdf_utils.salvar_pdf_como(
                "Ficha Cadastral do Aluno", blocos_pdf(),
                f"Ficha_Aluno_{dados.get('nome','').replace(' ','_')}.pdf",
                parent=form)

        def impr_acao():
            pdf_utils.imprimir_pdf(
                "Ficha Cadastral do Aluno", blocos_pdf(),
                f"Ficha_Aluno_{dados.get('nome','').replace(' ','_')}.pdf",
                parent=form)

        # ── Botões na barra inferior ──────────────────────────────────────
        ctk.CTkButton(bb, text="✖ Fechar",
                      fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"],
                      text_color=CORES["texto_claro"],
                      command=form.destroy,
                      width=110, height=38).pack(side="right", padx=10, pady=10)

        if not somente_visualizar:
            ctk.CTkButton(bb, text="💾 Salvar",
                          fg_color=CORES["acento"], hover_color=CORES["acento_hover"],
                          text_color=CORES["texto_claro"], font=fonte(13, "bold"),
                          command=salvar,
                          width=130, height=38).pack(side="right", padx=6, pady=10)
        elif aluno_id and not self.somente_consulta:
            def _abrir_em_edicao():
                form.destroy()
                self._abrir_form(aluno_id, somente_visualizar=False)
            ctk.CTkButton(bb, text="✏ Editar",
                          fg_color=CORES["primaria_clara"], text_color=CORES["texto_claro"],
                          font=fonte(13, "bold"), command=_abrir_em_edicao,
                          width=110, height=38).pack(side="right", padx=6, pady=10)

        ctk.CTkButton(bb, text="🖨 Imprimir",
                      fg_color=CORES["primaria_clara"],
                      text_color=CORES["texto_claro"],
                      command=impr_acao,
                      width=120, height=38).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(bb, text="📄 Salvar PDF",
                      fg_color=CORES["dourado"], hover_color=CORES["dourado_hover"],
                      text_color=CORES["sidebar"], font=fonte(12, "bold"),
                      command=pdf_acao,
                      width=130, height=38).pack(side="left", padx=6, pady=10)

        if aluno_id:
            def abrir_matricula():
                from modules.matriculas_shared import abrir_dialogo_matricula
                abrir_dialogo_matricula(form, aluno_id, dados.get("nome", ""),
                                        on_concluido=lambda: messagebox.showinfo(
                                            "Enviado", "Aluno enviado para a aba Matrículas e Rematrículas!",
                                            parent=form))
            ctk.CTkButton(bb, text="📝 Matrícula/Rematrícula",
                          fg_color=CORES["secundaria"], hover_color=CORES["primaria_clara"],
                          text_color=CORES["texto_claro"], font=fonte(12, "bold"),
                          command=abrir_matricula,
                          width=190, height=38).pack(side="left", padx=6, pady=10)

        # Botões SEED — Requerimentos oficiais
        def _dados_para_requerimento():
            """Coleta dados atuais da tela para o requerimento."""
            d = coletar()
            d["turma_var"] = self.turma_var.get()

            # Série / Turma (letra) / Turno separados — usados por documentos
            # que precisam desses campos individualmente (ex: Autorização de Imagem)
            turma_id_sel = self.t_dict.get(self.turma_var.get())
            if turma_id_sel:
                conn_t = get_connection()
                turma_row = conn_t.execute(
                    "SELECT serie, letra, turno FROM turmas WHERE id=?", (turma_id_sel,)
                ).fetchone()
                conn_t.close()
                if turma_row:
                    d["serie"] = turma_row["serie"] or ""
                    d["turma_letra"] = turma_row["letra"] or ""
                    d["turno"] = turma_row["turno"] or ""
            d.setdefault("serie", "")
            d.setdefault("turma_letra", "")
            d.setdefault("turno", "")

            # Buscar nome, CNPJ e Mantenedora da escola
            conn_e = get_connection()
            escola_row = conn_e.execute("SELECT nome_escola, cnpj, mantenedora FROM dados_escola LIMIT 1").fetchone()
            conn_e.close()
            if escola_row:
                d["_escola"] = escola_row["nome_escola"] or "Escola Municipal TRÁ LÁ LÁ"
                d["_cnpj_escola"] = escola_row["cnpj"] or ""
                d["_mantenedora"] = escola_row["mantenedora"] or ""
            else:
                d["_escola"] = "Escola Municipal TRÁ LÁ LÁ"
                d["_cnpj_escola"] = ""
                d["_mantenedora"] = ""
            return d

        def gerar_matricula():
            salvar_requerimento("matricula", _dados_para_requerimento(),
                                _dados_para_requerimento()["_escola"], parent=form)

        def gerar_renovacao():
            salvar_requerimento("renovacao", _dados_para_requerimento(),
                                _dados_para_requerimento()["_escola"], parent=form)

        # Frame para os botões SEED (segunda linha da barra)
        bb2 = ctk.CTkFrame(form, fg_color=CORES["card_claro"], corner_radius=0, height=46)
        bb2.pack(fill="x", side="bottom")
        bb2.pack_propagate(False)

        ctk.CTkLabel(bb2, text="📋 Requerimentos SEED-PR:",
                     font=fonte(11, "bold"),
                     text_color=CORES["subtexto"]).pack(side="left", padx=12, pady=10)

        ctk.CTkButton(bb2, text="📝 Gerar Requerimento de Matrícula",
                      fg_color=CORES["secundaria"],
                      text_color=CORES["texto_claro"],
                      font=fonte(11, "bold"),
                      command=gerar_matricula,
                      width=250, height=30).pack(side="left", padx=6, pady=8)

        ctk.CTkButton(bb2, text="🔄 Gerar Renovação de Matrícula",
                      fg_color=CORES["primaria"],
                      text_color=CORES["texto_claro"],
                      font=fonte(11, "bold"),
                      command=gerar_renovacao,
                      width=240, height=30).pack(side="left", padx=6, pady=8)

        def gerar_saude():
            gerar_documento_word("saude", _dados_para_requerimento(), parent=form)

        ctk.CTkButton(bb2, text="🏥 Ficha de Saúde",
                      fg_color="#1e7e34",
                      text_color=CORES["texto_claro"],
                      font=fonte(11, "bold"),
                      command=gerar_saude,
                      width=180, height=30).pack(side="left", padx=6, pady=8)

        def gerar_autorizacao_imagem():
            gerar_documento_word("autorizacao_imagem", _dados_para_requerimento(), parent=form)

        ctk.CTkButton(bb2, text="📸 Autorização de Uso de Imagem",
                      fg_color="#8e44ad",
                      text_color=CORES["texto_claro"],
                      font=fonte(11, "bold"),
                      command=gerar_autorizacao_imagem,
                      width=250, height=30).pack(side="left", padx=6, pady=8)


        ctk.CTkLabel(bb, text="Sistema desenvolvido por João Paulo A. Guaita - Licença de uso cedida gratuitamente",
                     font=fonte(11), text_color=CORES["subtexto"]).pack(side="left", padx=15)
