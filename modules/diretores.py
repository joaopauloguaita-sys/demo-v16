import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.pessoa_funcional import PessoaFuncionalModule

class DiretoresModule(PessoaFuncionalModule):
    def __init__(self, parent, somente_consulta=False, **kwargs):
        super().__init__(parent, tabela="diretores", titulo="Diretores(as)", icone="🏛",
                          mostrar_disciplinas=False, somente_consulta=somente_consulta,
                          mostrar_portaria=True, tem_atestados=True, **kwargs)
