import carta

class Mao:
    def __init__(self):
        self.cartas = [] # vetor preenchido de objetos do tipo Carta
        
    def __str__(self):
        if len(self.cartas) > 0:
            return ' | '.join(str(carta) for carta in self.cartas)
        else:
            return "Mão vazia"
                
    def recebe_carta(self, carta):
        self.cartas.append(carta)
        
    def joga_carta(self):
        if len(self.cartas) > 0:
            return self.cartas.pop(0)
        # so pra debug, nao deveria chegar ate aqui no mundo ideal
        return "todas as cartas foram jogadas"
    
    # indica quais cartas dessa mao sao manilhas
    # se for manilha, o valor usado pra comparar qual a maior carta é o valorManilha
    def verifica_manilhas(self, cartaVirada):
        for carta in self.cartas:
            if carta.valorPadrao == cartaVirada.manilha():
                carta.ehManilha = True