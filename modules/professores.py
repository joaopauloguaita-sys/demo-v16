import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.pessoa_funcional import PessoaFuncionalModule


class ProfessoresModule(PessoaFuncionalModule):
    def __init__(self, parent, somente_consulta=False):
        super().__init__(parent, tabela="professores", titulo="Professores", icone="👨‍🏫",
                          mostrar_disciplinas=True, somente_consulta=somente_consulta)
