class Carta:
    # cartas = ["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"]
    # naipe = ["Ouros", "Copas", "Espadas", "Paus"]
    
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
    
    naipes = {
        "Ouros": 1,
        "Espadas": 2,
        "Copas": 3,
        "Paus": 4
    }
    
    def __init__(self, carta, naipe):
        self.carta = carta
        self.naipe = naipe
        self.valorPadrao = Carta.grandeza[carta] 
        self.ehManilha = False # se for manilha, a cada rodada esse valor é alterado
        self.valorManilha = self.valorPadrao + Carta.naipes[naipe] + 100 
        
    def __str__(self):
        if self.ehManilha:
            return f"{self.carta} de {self.naipe} -- {self.apelido()}"
        return f"{self.carta} de {self.naipe}"
    
    def apelido(self):
        if self.naipe == "Ouros":
            return "MOLE"
        if self.naipe == "Espadas":
            return "ESPADILHA"
        if self.naipe == "Copas":
            return "COPAS"
        if self.naipe == "Paus":
            return "GATO"
    
    # retorna o valor da manilha dessa carta
    # ex: 5 é manilha de 4 e tem valor 10, 4 é manilha de 3 e tem valor 0
    def manilha(self):
        if self.carta == "3":
            return 0
        return self.valorPadrao + 10