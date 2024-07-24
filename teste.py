import baralho
import carta
import mao
import jogador
import verificador

def imprime_carta_galera(jogadores):
    print("---------------------- imprime cartas ---------------------")    
    for jogador in jogadores:
        if jogador.mao.cartas == []:
            return
        print()
        print("Cartas do jogador:", jogadores.index(jogador) + 1)
        print(jogador.mao)
    print("-----------------------------------------------------------")    
    print()    

instanciaBaralho = baralho.Baralho()
instanciaBaralho.embaralhar()

# cria jogadores
jogadores = [jogador.Jogador(str(i+1)) for i in range(4)]

# distribui cartas
for i in range(3):
    for jogador in jogadores:
        jogador.mao.recebe_carta(instanciaBaralho.entrega_carta())

# pega manilha
cartaVirada = instanciaBaralho.entrega_carta()

print(f"Carta virada: {cartaVirada}")

# indica as cartas que sao manilha na mao dos jogadores
for jogador in jogadores:
    jogador.mao.verifica_manilhas(cartaVirada)
print()
conta_rodadas = 1

# logica do jogo
while not all(jogador.mao.cartas == [] for jogador in jogadores):    
    print()
    print(f"====================== comeca rodada {conta_rodadas} ======================")    
    # mostra mao dos jogadores
    imprime_carta_galera(jogadores)

    instanciaVerificador = verificador.Verificador()

    for jogador in jogadores:
        cartaJogada = jogador.mao.joga_carta()
        instanciaVerificador.bota_carta_na_mesa(cartaJogada, jogador)
        print(f"{jogador.nome} jogou a carta {cartaJogada}")
        instanciaVerificador.narrador()

    print(instanciaVerificador)
    conta_rodadas += 1

    # verificar se embuchou
    # talvez usar uma lista circular pra manter os jogadores (isso facilita achar o jogador da direita)    
    # quem inicia
    # manter dado do jogador que esta ganhando a mao
    # adicionar metodo para controlar valores das cartas
    # adicionar metodo para controlar quem ganhou a mao
    # adicionar metodo para controlar palpites (verificar se obrigatoriamente alguem vai se ferrar)
    # adicionar metodo para controlar as vidas dos jogadores
    
    