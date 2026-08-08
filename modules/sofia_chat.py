import json
import os
import sys
import threading
from datetime import datetime, date
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import requests
import io
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection
from tema import fonte, CORES
from modules import sofia_tools

# --- CONFIGURAÇÕES DE IA ---
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELO_VISAO = "llama-3.2-11b-vision-preview"
MODELO_TEXTO = "llama-3.3-70b-versatile" # O modelo mais potente e recente

# NOVO PROMPT: Sem apresentações repetitivas e mais atual
SYSTEM_PROMPT = (
    "Você é a SofIA, uma assistente virtual inteligente e prestativa. "
    "Sua personalidade é natural, direta e humana. Não use saudações robóticas ou repetitivas. "
    "IDENTIDADE: Somente diga que foi criada por 'João Paulo A. Guaita' se o usuário te perguntar 'quem é você' ou 'quem te criou'. "
    "CONHECIMENTO: Você tem informações atualizadas. Se o usuário perguntar sobre algo muito recente (ex: 2024 ou 2025) que você não tenha certeza, "
    "não diga apenas 'não sei'. Em vez disso, peça gentilmente para o usuário anexar o arquivo ou o Diário Oficial pelo ícone de CLIPE (📎) "
    "para que você possa ler e analisar os dados em tempo real para ele.\n\n"
    "FERRAMENTAS DO SISTEMA: Você tem acesso a ferramentas que consultam o banco de dados real "
    "da escola (buscar_pessoa, horario_atual, faltas_aluno). Use essas ferramentas sempre que a "
    "pergunta envolver um dado específico do sistema — telefone, RG, CPF, cargo, turma de alguém, "
    "qual aula uma turma tem agora, ou faltas de um aluno. NUNCA invente esses dados; se a "
    "ferramenta não encontrar a pessoa/turma, diga isso claramente ao usuário."
)

COR_FUNDO_PRINCIPAL = "#161616"
COR_FUNDO_SIDEBAR = "#111111"
COR_FUNDO_CHAT = "#1c1c1c"
COR_AZUL = "#2b6cb0"

class SofiaChatModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COR_FUNDO_PRINCIPAL)
        
        self.pasta_dados = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dados_sofia")
        os.makedirs(self.pasta_dados, exist_ok=True)
        self.arquivo_conversas = os.path.join(self.pasta_dados, "conversas.json")
        
        self.contexto_arquivo = ""
        self.dados_conversas = self._carregar_conversas()
        
        if not self.dados_conversas.get("conversas"): self._criar_conversa_vazia()
        self.conversa_ativa_id = self.dados_conversas["ativa"]
        self.mensagens = self.dados_conversas["conversas"][self.conversa_ativa_id]["mensagens"]

        self._build_ui()
        self._reconstruir_chat_visual()
        threading.Thread(target=self._pre_aquecer_rag, daemon=True).start()

    def _pre_aquecer_rag(self):
        """Carrega o modelo de embeddings do RAG em segundo plano assim que a tela
        abre, pra quando o usuário mandar a primeira pergunta ela já estar pronta."""
        try:
            from modules import rag
            if rag.total_documentos() > 0:
                rag._obter_modelo()
        except Exception:
            pass

    def _carregar_conversas(self):
        if os.path.exists(self.arquivo_conversas):
            try:
                with open(self.arquivo_conversas, "r", encoding="utf-8") as f: return json.load(f)
            except: pass
        return {"conversas": {}, "ativa": None}

    def _salvar_conversas(self):
        with open(self.arquivo_conversas, "w", encoding="utf-8") as f:
            json.dump(self.dados_conversas, f, ensure_ascii=False, indent=2)

    def _criar_conversa_vazia(self):
        id_c = datetime.now().strftime("%Y%m%d%H%M%S")
        self.dados_conversas = {"conversas": {id_c: {"mensagens": [], "titulo": "Nova Conversa"}}, "ativa": id_c}
        self._salvar_conversas()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, fg_color=COR_FUNDO_SIDEBAR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="🤖 SofIA", font=fonte(20, "bold"), text_color=COR_AZUL).pack(pady=20)
        ctk.CTkButton(self.sidebar, text="+ Nova Conversa", fg_color=COR_AZUL, command=self.nova_conversa).pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="🗑 Limpar Chat", fg_color="#c0392b", command=self.limpar_conversa).pack(pady=10, padx=20, fill="x")

        self.area_chat = ctk.CTkScrollableFrame(self, fg_color=COR_FUNDO_CHAT, corner_radius=0)
        self.area_chat.grid(row=0, column=1, sticky="nsew", padx=10, pady=(10, 0))

        self.rodape = ctk.CTkFrame(self, height=80, fg_color="transparent")
        self.rodape.grid(row=1, column=1, sticky="ew", padx=10, pady=10)

        self.btn_clipe = ctk.CTkButton(self.rodape, text="📎", width=45, height=45, fg_color="#333", command=self.anexar_geral)
        self.btn_clipe.pack(side="left", padx=5)

        self.entry_msg = ctk.CTkEntry(self.rodape, placeholder_text="Digite sua mensagem aqui...", height=45)
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_msg.bind("<Return>", lambda e: self.enviar_mensagem())

        self.btn_enviar = ctk.CTkButton(self.rodape, text="Enviar", width=80, height=45, fg_color=COR_AZUL, command=self.enviar_mensagem)
        self.btn_enviar.pack(side="right", padx=5)

    def anexar_geral(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos", "*.pdf *.docx *.txt *.jpg *.jpeg *.png")])
        if not caminho: return
        if caminho.lower().endswith(('.jpg', '.jpeg', '.png')):
            self._adicionar_bolha("🖼️ Analisando imagem...", True)
            threading.Thread(target=self._chamar_ia_visao, args=(caminho,), daemon=True).start()
        else:
            self._adicionar_bolha(f"📄 Lendo arquivo...", True)
            threading.Thread(target=self._processar_documento, args=(caminho,), daemon=True).start()

    def _processar_documento(self, caminho):
        try:
            from modules import rag
            texto = rag.extrair_texto(caminho)
            self.contexto_arquivo = f"\n[CONTEÚDO DO DOCUMENTO ANEXADO]: {texto[:8000]}"
            self.after(0, lambda: self._adicionar_bolha("Li o documento com sucesso. O que você gostaria de saber sobre ele?", False))
        except Exception as e: 
            self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao ler: {e}"))

    def enviar_mensagem(self):
        texto = self.entry_msg.get().strip()
        if not texto: return
        self.entry_msg.delete(0, "end")
        self._adicionar_bolha(texto, usuario=True)
        self._bolha_digitando = self._adicionar_bolha("💭 Pensando...", False)

        # Se houver documento na memória, anexa ao prompt
        prompt_enviar = texto
        if self.contexto_arquivo:
            prompt_enviar = f"{self.contexto_arquivo}\n\nPERGUNTA DO USUÁRIO: {texto}"
            self.contexto_arquivo = "" # Limpa a memória após o envio

        self.mensagens.append({"role": "user", "content": texto})
        threading.Thread(target=self._chamar_ia, args=(prompt_enviar,), daemon=True).start()

    def _chamar_ia_visao(self, caminho_img):
        api_key = self._get_api_key()
        try:
            with open(caminho_img, "rb") as f:
                b64_image = base64.b64encode(f.read()).decode('utf-8')
            payload = {
                "model": MODELO_VISAO,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": "Transcreva este documento ou descreva esta imagem."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                ]}]
            }
            resp = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {api_key}"}, json=payload)
            res = resp.json()["choices"][0]["message"]["content"]
            self.after(0, lambda: self._finalizar_ia(res))
        except Exception as e:
            self.after(0, lambda: self._adicionar_bolha(f"Erro na visão: {e}", False))

    def _chamar_ia(self, prompt_final):
        api_key = self._get_api_key()
        if not api_key:
            self.after(0, lambda: self._finalizar_ia(
                "Não encontrei a chave da API configurada em Dados da Escola."))
            return
        try:
            # 1) Busca na Base de Conhecimento (RAG) — só entra no contexto se achar algo
            # claramente relevante, e só pra perguntas com conteúdo de verdade (evita
            # carregar o modelo de embeddings à toa pra "oi", "obrigado", etc.)
            contexto_rag = ""
            texto_pergunta = prompt_final.strip()
            vale_a_pena_buscar = len(texto_pergunta) >= 12
            if vale_a_pena_buscar:
                try:
                    from modules import rag
                    if rag.total_documentos() > 0:
                        trechos = rag.buscar(texto_pergunta, top_k=3, limiar_minimo=0.45)
                        if trechos:
                            blocos = "\n\n".join(
                                f"(trecho de {t['documento']}): {t['texto']}" for t in trechos)
                            contexto_rag = (
                                "\n\n[POSSÍVEIS TRECHOS RELEVANTES DA BASE DE CONHECIMENTO — "
                                "use APENAS se realmente responderem a pergunta do usuário; "
                                "se não tiverem relação nenhuma com a pergunta, ignore "
                                f"completamente e responda normalmente]:\n{blocos}"
                            )
                except Exception:
                    pass  # se o RAG falhar por algum motivo, segue sem ele em vez de travar o chat

            mensagens = (
                [{"role": "system", "content": SYSTEM_PROMPT + f"\n\nA data de hoje é {date.today().strftime('%d/%m/%Y')} ({date.today().isoformat()}). "
                  "Use isso pra calcular períodos relativos (ex: 'esse mês', 'esse ano', 'desde dia 16 do "
                  "mês passado') antes de chamar as ferramentas de atestados/ocorrências, passando datas "
                  "exatas no formato AAAA-MM-DD."}]
                + self.mensagens[-6:-1]
                + [{"role": "user", "content": prompt_final + contexto_rag}]
            )

            resposta_final = self._chamar_groq(mensagens, permitir_ferramentas=True)
            self.after(0, lambda: self._finalizar_ia(resposta_final))
        except Exception as e:
            erro_str = str(e)
            if erro_str.startswith("LIMITE_DIARIO:"):
                self.after(0, lambda: self._finalizar_ia(
                    "😅 " + erro_str.replace("LIMITE_DIARIO: ", "")))
            else:
                self.after(0, lambda: self._finalizar_ia(
                    "Estou com dificuldade de conexão. Tente novamente em instantes."))

    def _chamar_groq(self, mensagens, permitir_ferramentas=False, profundidade=0):
        """Chama a API da Groq. Se o modelo pedir pra usar uma ferramenta do banco,
        executa localmente e faz uma nova chamada com o resultado — até no máximo
        3 idas e voltas, pra nunca travar num loop."""
        api_key = self._get_api_key()
        payload = {"model": MODELO_TEXTO, "messages": mensagens}
        if permitir_ferramentas and profundidade < 3:
            payload["tools"] = sofia_tools.FERRAMENTAS
            payload["tool_choice"] = "auto"

        resp = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {api_key}"},
                             json=payload, timeout=30)
        if resp.status_code == 429:
            raise RuntimeError(
                "LIMITE_DIARIO: Você atingiu o limite diário gratuito de uso da IA. "
                "Aguarde um pouco (geralmente libera em minutos) ou peça pra alguém "
                "aumentar o plano em console.groq.com/settings/billing.")
        if resp.status_code != 200:
            raise RuntimeError(f"Groq API respondeu {resp.status_code}: {resp.text[:400]}")
        corpo = resp.json()
        if "choices" not in corpo:
            raise RuntimeError(f"Resposta inesperada da Groq: {str(corpo)[:400]}")
        msg = corpo["choices"][0]["message"]

        tool_calls = msg.get("tool_calls")
        if tool_calls:
            mensagens = mensagens + [msg]
            for chamada in tool_calls:
                nome_funcao = chamada["function"]["name"]
                try:
                    argumentos = json.loads(chamada["function"]["arguments"] or "{}")
                except Exception:
                    argumentos = {}
                resultado = sofia_tools.executar_ferramenta(nome_funcao, argumentos)
                mensagens.append({
                    "role": "tool",
                    "tool_call_id": chamada["id"],
                    "name": nome_funcao,
                    "content": json.dumps(resultado, ensure_ascii=False),
                })
            return self._chamar_groq(mensagens, permitir_ferramentas=True, profundidade=profundidade + 1)

        return msg.get("content", "")

    def _finalizar_ia(self, resposta):
        if getattr(self, "_bolha_digitando", None) is not None:
            try:
                self._bolha_digitando.destroy()
            except Exception:
                pass
            self._bolha_digitando = None
        self._adicionar_bolha(resposta, False)
        self.mensagens.append({"role": "assistant", "content": resposta})
        self._salvar_conversas()

    def _get_api_key(self):
        try:
            conn = get_connection()
            row = conn.execute("SELECT gemini_api_key FROM dados_escola LIMIT 1").fetchone()
            conn.close()
            return row[0] if row and row[0] else None
        except: return None

    def _adicionar_bolha(self, texto, usuario=True):
        cor = COR_AZUL if usuario else "#2a2a2a"
        lbl = ctk.CTkLabel(self.area_chat, text=texto, fg_color=cor, text_color="white", corner_radius=12, 
                           wraplength=550, padx=15, pady=10, justify="left", font=fonte(12))
        lbl.pack(anchor="e" if usuario else "w", pady=8, padx=10)
        self.after(10, lambda: self.area_chat._parent_canvas.yview_moveto(1.0))
        return lbl

    def _reconstruir_chat_visual(self):
        for w in self.area_chat.winfo_children(): w.destroy()
        if not self.mensagens:
            self._adicionar_bolha("Olá! Como posso ajudar a escola hoje?", False)
        else:
            for m in self.mensagens: self._adicionar_bolha(m["content"], m["role"] == "user")

    def nova_conversa(self):
        self._criar_conversa_vazia()
        self.conversa_ativa_id = self.dados_conversas["ativa"]
        self.mensagens = []
        self._reconstruir_chat_visual()

    def limpar_conversa(self):
        if messagebox.askyesno("Limpar", "Deseja apagar o histórico atual?"):
            self.mensagens.clear()
            self._reconstruir_chat_visual()
            self._salvar_conversas()