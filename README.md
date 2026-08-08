# 🏫 EscolaGest — Sistema de Gestão Escolar

Sistema desktop de gestão para secretaria escolar desenvolvido em Python.

---

## 📋 Módulos disponíveis

| Módulo | Descrição |
|--------|-----------|
| 🏠 Dashboard | Visão geral com estatísticas e atalhos |
| 🎓 Alunos | Cadastro completo de alunos |
| 👨‍🏫 Professores | Cadastro de professores e disciplinas |
| 🏫 Turmas | Gerenciamento de turmas e grade horária |
| 📚 Disciplinas | Cadastro de disciplinas por turma |
| 📊 Notas | Lançamento de notas e boletins |
| ✅ Frequência | Chamada diária e histórico de presença |
| 📄 Relatórios | 9 tipos de relatórios exportáveis |

---

## 🚀 Instalação — Passo a Passo

### Pré-requisito: Python

1. Acesse **https://python.org/downloads**
2. Clique em **"Download Python 3.x.x"**
3. Execute o instalador
4. ⚠️ **IMPORTANTE:** marque a caixa **"Add Python to PATH"** antes de instalar
5. Clique em "Install Now"

### Instalando o EscolaGest

1. Baixe ou clone esta pasta **EscolaGest**
2. Abra a pasta
3. Dê **duplo clique** no arquivo **`instalar.bat`**
4. Aguarde a instalação (aparecerá "Instalação concluída!")

### Iniciando o sistema

- Dê **duplo clique** em **`iniciar.bat`**
- A tela de login aparecerá

**Login padrão:**
- Usuário: `admin`
- Senha: `admin123`

---

## 📁 Estrutura do projeto

```
EscolaGest/
├── main.py              ← Arquivo principal (executar este)
├── iniciar.bat          ← Atalho para Windows
├── instalar.bat         ← Instalador de dependências
├── requirements.txt     ← Lista de dependências
├── database/
│   ├── db.py            ← Banco de dados SQLite
│   └── escola.db        ← Criado automaticamente
└── modules/
    ├── alunos.py        ← Módulo de alunos
    ├── professores.py   ← Módulo de professores
    ← turmas.py          ← Módulo de turmas e horários
    ├── disciplinas.py   ← Módulo de disciplinas
    ├── notas.py         ← Módulo de notas
    ├── frequencia.py    ← Módulo de frequência
    └── relatorios.py    ← Módulo de relatórios
```

---

## 🌐 Uso em rede (vários computadores)

Para que múltiplos computadores acessem o mesmo banco de dados:

1. Escolha **um computador** como "servidor" (onde ficará o banco)
2. Coloque a pasta **EscolaGest** em uma pasta compartilhada na rede
3. Nos outros computadores, abra o caminho de rede e execute `iniciar.bat`
4. Todos acessarão o mesmo arquivo `escola.db`

---

## 🔄 Ordem recomendada de cadastro

1. **Professores** → cadastre os professores primeiro
2. **Turmas** → crie as turmas e associe professores
3. **Disciplinas** → crie disciplinas e vincule às turmas
4. **Alunos** → cadastre alunos e associe às turmas
5. **Horários** → monte a grade na tela de Turmas
6. **Notas e Frequência** → use no dia a dia

---

## 💾 Backup

O banco de dados fica no arquivo `database/escola.db`.
Para fazer backup, basta copiar este arquivo para outro local.

---

## 🛠️ Tecnologias utilizadas

- **Python 3.x** — Linguagem de programação
- **CustomTkinter** — Interface gráfica moderna
- **SQLite** — Banco de dados (sem instalação extra)
- **Tkinter TTK** — Componentes de tabela

---

## 📞 Suporte

Desenvolvido com assistência do Claude (Anthropic).
Para dúvidas ou melhorias, abra uma Issue no GitHub.
