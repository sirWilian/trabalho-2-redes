from mao import Mao

class Jogador:
    def __init__(self, nome):
        self.nome = "Jogador"
        if isinstance(nome, str):
            self.nome = self.nome + f" {nome}" 
            
        self.mao = Mao()    # preenchido por objetos do tipo Mao
        self.vidas = 12     # vidas
        self.vitorias = 0   # partidas ganhas (talvez nem precise disso)
        
    def __str__(self):
        return f"{self.nome}"