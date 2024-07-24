class Verificador:
    def __init__(self):
        # controla cartas jogadas por todos nessa mao
        self.cartas = [] # vetor preenchido de objetos do tipo Carta
        self.donoMaiorCarta = None
        self.maiorCarta = None
        self.embuchada = False
    
    def bota_carta_na_mesa(self, carta, jogador):
        self.cartas.append(carta)
        # se for a primeira carta jogada, ela é a maior
        if len(self.cartas) == 1:
            self.maiorCarta = carta
            self.donoMaiorCarta = jogador
            return
        # se não for a primeira carta jogada, verifica se é a maior
        # primeiro verifica se a maior atual é manilha, se for, 
        # o valor de comparacao eh o self.valorManilha
        
        # caso as duas sejam manilhas
        if self.maiorCarta.ehManilha and carta.ehManilha:
            if carta.valorManilha > self.maiorCarta.valorManilha:
                self.maiorCarta = carta
                self.donoMaiorCarta = jogador
                self.embuchada = False
            return
        # caso a maior atual seja manilha e a carta jogada não seja
        elif self.maiorCarta.ehManilha and not carta.ehManilha:
            self.embuchada = False
            return
        # caso a maior atual não seja manilha e a carta jogada seja
        elif not self.maiorCarta.ehManilha and carta.ehManilha:
            self.maiorCarta = carta
            self.donoMaiorCarta = jogador
            self.embuchada = False
            return
        # caso nenhuma das duas seja manilha
        else:
            if carta.valorPadrao > self.maiorCarta.valorPadrao:
                self.maiorCarta = carta
                self.donoMaiorCarta = jogador
                self.embuchada = False
                return
            # caso as duas cartas tenham o mesmo valor (embucha)
            elif carta.valorPadrao == self.maiorCarta.valorPadrao:
                self.embuchada = True
                return
    
    def narrador(self):
        if self.embuchada:
            print("ta embuchada!")
            print()
            return
        print(self.donoMaiorCarta, "ta fazendo com", self.maiorCarta)
        print()
    
    def __str__(self):
        if self.embuchada:
            return "Embuchou!"
        return f"{self.donoMaiorCarta} fez com {self.maiorCarta}"