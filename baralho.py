import random
from carta import Carta

class Baralho:
    # Criando o baralho
    def __init__(self):
        # Definindo os naipes e as cartas
        naipes = ['Ouros', 'Espadas', 'Copas', 'Paus']
        cartas = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        self.baralho = [Carta(carta, naipe) for naipe in naipes for carta in cartas]
        self.ordena_baralho_por_carta()
        
    def __str__(self):
        return '\n'.join(str(carta) for carta in self.baralho)

    def ordena_baralho_por_carta(self):
        
        grandeza = {
            "4": 0,
            "5": 10,
            "6": 20,
            "7": 30,
            "Q": 40,
            "J": 50,
            "K": 60,
            "A": 70,
            "2": 80,
            "3": 90
        }
        
        # Ordenando o baralho pelas cartas
        self.baralho = sorted(self.baralho, key=lambda x: grandeza[x.carta])
        
    def embaralhar(self):
        random.shuffle(self.baralho)
    
    def entrega_carta(self):
        return self.baralho.pop(0)
    
# --------------------------------------------------------------------------------------
