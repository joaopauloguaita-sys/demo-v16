import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.pessoa_funcional import PessoaFuncionalModule


class SecretariosModule(PessoaFuncionalModule):
    def __init__(self, parent, somente_consulta=False, **kwargs):
        super().__init__(parent, tabela="secretarios", titulo="Secretário(a)", icone="🗂️",
                          mostrar_disciplinas=False, somente_consulta=somente_consulta, **kwargs)
