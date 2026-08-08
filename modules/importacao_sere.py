import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import sys, os, re
import pandas as pd
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import CORES, fonte

# ============================================================
# LÓGICA DE EXTRAÇÃO PRECISA SERE-PR
# ============================================================

def _limpar(val):
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '']: return ""
    return str(val).strip()

def ler_arquivo_sere(caminho):
    try:
        # Lê o Excel varrendo tudo
        df = pd.read_excel(caminho, header=None).fillna('')
        linhas = df.values.tolist()
        
        alunos = []
        seriacao = ""
        letra_turma = ""
        
        # 1. VARREDURA PARA TURMA E CABEÇALHO
        idx_cgm = idx_nome = idx_nasc = idx_sexo = idx_tel = idx_rg = idx_cpf = -1
        header_row_index = -1

        for i, row in enumerate(linhas):
            row_str = [str(c).upper().strip() for c in row]
            
            # Captura a Turma no topo (Ex: Seriação: 5º Ano / Turma: A)
            for cell in row_str:
                if "SERIAÇÃO:" in cell: seriacao = cell.split("SERIAÇÃO:")[-1].strip()
                if "TURMA:" in cell: letra_turma = cell.split("TURMA:")[-1].strip()

            # Localiza o cabeçalho exato baseado na imagem do SERE-PR
            if "CGM" in row_str and "NOME DO ESTUDANTE" in row_str:
                header_row_index = i
                for idx, cell in enumerate(row_str):
                    if "CGM" == cell: idx_cgm = idx
                    if "NOME DO ESTUDANTE" in cell: idx_nome = idx
                    if "DATA DE" in cell: idx_nasc = idx
                    if "SE" == cell: idx_sexo = idx # No SERE "SE" é Sexo
                    if "TELEFONE" in cell: idx_tel = idx
                    if "RG" == cell: idx_rg = idx
                    if "CPF" == cell: idx_cpf = idx
                break

        if header_row_index == -1:
            return [], "Não encontrei as colunas 'CGM' e 'Nome do Estudante'. Verifique o arquivo."

        # 2. EXTRAÇÃO DOS ALUNOS
        for j in range(header_row_index + 1, len(linhas)):
            r = linhas[j]
            cgm_bruto = str(r[idx_cgm]).split('.')[0].strip() if idx_cgm != -1 else ""
            if not cgm_bruto.isdigit() or len(cgm_bruto) < 5: continue

            # Formata Data de Nascimento
            nasc_bruto = _limpar(r[idx_nasc])
            nasc_final = ""
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y'):
                try: 
                    nasc_final = datetime.strptime(nasc_bruto.split(' ')[0], fmt).strftime('%Y-%m-%d')
                    break
                except: pass

            # Traduz Sexo
            sexo_raw = str(r[idx_sexo]).upper().strip()
            sexo = "Masculino" if sexo_raw == "M" else "Feminino" if sexo_raw == "F" else ""

            alunos.append({
                'cgm': cgm_bruto,
                'nome': _limpar(r[idx_nome]).upper(),
                'data_nascimento': nasc_final,
                'sexo': sexo,
                'telefone': _limpar(r[idx_tel]),
                'rg': _limpar(r[idx_rg]),
                'cpf': _limpar(r[idx_cpf]),
                'turma_sere': f"{seriacao} {letra_turma}".strip()
            })

        return alunos, None
    except Exception as e:
        return [], str(e)

# ============================================================
# INTERFACE COM TODAS AS COLUNAS VISÍVEIS
# ============================================================

class ImportacaoSereModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=CORES["fundo"])
        self._alunos_preview = []
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(header, text="📥 Importação SERE-PR", font=fonte(22, "bold"), text_color=CORES["dourado"]).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(header, text="📁 Selecionar Arquivo(s)", command=self._selecionar, width=200).pack(side="right", padx=20)

        tabela_f = ctk.CTkFrame(self, fg_color=CORES["card"], corner_radius=12)
        tabela_f.pack(fill="both", expand=True, padx=20, pady=10)

        # Adicionadas colunas extras no preview visual
        cols = ("cgm", "nome", "nasc", "sexo", "tel", "rg", "cpf", "turma", "status")
        self.tree = ttk.Treeview(tabela_f, columns=cols, show="headings")
        
        config = [
            ("cgm", "CGM", 90), ("nome", "Nome", 220), ("nasc", "Nasc.", 85),
            ("sexo", "Sexo", 75), ("tel", "Telefone", 100), ("rg", "RG", 90),
            ("cpf", "CPF", 100), ("turma", "Turma", 100), ("status", "Status", 80)
        ]
        for cid, txt, larg in config:
            self.tree.heading(cid, text=txt)
            self.tree.column(cid, width=larg)

        self.tree.tag_configure("novo", foreground="#1565c0")
        self.tree.tag_configure("existente", foreground="#2e7d32")
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbars
        v_sc = ttk.Scrollbar(tabela_f, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=v_sc.set); v_sc.pack(side="right", fill="y")
        h_sc = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview); self.tree.configure(xscrollcommand=h_sc.set); h_sc.pack(fill="x", padx=20)

        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=(5, 15))
        
        self.label_info = ctk.CTkLabel(btn_f, text="Aguardando arquivo...", font=fonte(12, "bold"))
        self.label_info.pack(side="left", padx=10)

        self.btn_executar = ctk.CTkButton(btn_f, text="✅ IMPORTAR / ATUALIZAR TUDO", fg_color="#27ae60", hover_color="#219150", 
                                          height=45, font=fonte(13, "bold"), state="disabled", command=self._importar_para_banco)
        self.btn_executar.pack(side="right", padx=10)

    def _selecionar(self):
        caminhos = filedialog.askopenfilenames(filetypes=[("Arquivos Excel", "*.xls *.xlsx")])
        if not caminhos: return
        todos = []
        for c in caminhos:
            alunos, erro = ler_arquivo_sere(c)
            if not erro: todos.extend(alunos)
        self._alunos_preview = todos
        self._atualizar_ui()

    def _atualizar_ui(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_connection()
        cgms = [str(r[0]) for r in conn.execute("SELECT cgm FROM alunos").fetchall()]
        conn.close()

        novos = 0
        for a in self._alunos_preview:
            existe = str(a['cgm']) in cgms
            tag = "existente" if existe else "novo"
            if not existe: novos += 1
            self.tree.insert("", "end", values=(a['cgm'], a['nome'], a['data_nascimento'], a['sexo'], a['telefone'], a['rg'], a['cpf'], a['turma_sere'], "Ok"), tags=(tag,))
        self.label_info.configure(text=f"Total: {len(self._alunos_preview)} | Novos: {novos}")
        if self._alunos_preview: self.btn_executar.configure(state="normal")

    def _importar_para_banco(self):
        if not self._alunos_preview: return
        if not messagebox.askyesno("Confirmar", "Deseja processar? Dados em branco no Excel não apagarão o que você já tem no sistema."): return

        conn = get_connection(); cursor = conn.cursor()
        turmas_sistema = {t['nome_completo'].upper(): t['id'] for t in conn.execute("SELECT id, nome_completo FROM turmas").fetchall()}
        
        processados = 0
        for a in self._alunos_preview:
            try:
                t_id = turmas_sistema.get(a['turma_sere'].upper())
                cursor.execute("SELECT id FROM alunos WHERE cgm = ?", (a['cgm'],))
                if cursor.fetchone():
                    # UPDATE PROTEGIDO (Item por item com CASE WHEN)
                    cursor.execute("""
                        UPDATE alunos SET 
                        nome = ?, 
                        data_nascimento = CASE WHEN ? != '' THEN ? ELSE data_nascimento END, 
                        sexo = CASE WHEN ? != '' THEN ? ELSE sexo END, 
                        turma_id = COALESCE(?, turma_id),
                        telefone_responsavel = CASE WHEN ? != '' THEN ? ELSE telefone_responsavel END,
                        rg = CASE WHEN ? != '' THEN ? ELSE rg END,
                        cpf = CASE WHEN ? != '' THEN ? ELSE cpf END,
                        ativo = 1, arquivado = 0
                        WHERE cgm = ?
                    """, (a['nome'], a['data_nascimento'], a['data_nascimento'], a['sexo'], a['sexo'], t_id, 
                          a['telefone'], a['telefone'], a['rg'], a['rg'], a['cpf'], a['cpf'], a['cgm']))
                else:
                    # NOVO ALUNO
                    cursor.execute("""
                        INSERT INTO alunos (cgm, nome, data_nascimento, sexo, turma_id, telefone_responsavel, rg, cpf, ativo, arquivado) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0)
                    """, (a['cgm'], a['nome'], a['data_nascimento'], a['sexo'], t_id, a['telefone'], a['rg'], a['cpf']))
                processados += 1
            except Exception as e: print(f"Erro no CGM {a['cgm']}: {e}")

        conn.commit(); conn.close()
        messagebox.showinfo("Sucesso", f"Processo concluído! {processados} alunos atualizados.")
        self.btn_executar.configure(state="disabled")