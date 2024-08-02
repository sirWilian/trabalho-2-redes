import jogador
import socket
import threading
import time

porta = 44445
BUFFER_SIZE = 1024

class Maquina:
    def __init__(self, ip, nome):
        self.ip = ip
        self.jogador = jogador.Jogador(nome) 
        # ip da proxima maquina. deve ser preenchido apos uma 
        # maquina entrar na rede. As maquinas entram na rede 
        # executando o programa e mandando uma mensagem na rede.
        # caso houver maquinas na rede. uma dessas maquinas deve verificar
        # o conjunto de maquinas, indicar qual posicao essa nova maquina assumirá,
        # indicar qual sera o ip da proxima maquina dela e incrementar o conjunto de maqs.
        self.prox = None 
        self.amigos = None
        
    # procura por maquinas na rede
    def manda_broadcast(self, ip_broadcast, porta_broadcast):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_socket:
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            mensagem = "busca-se amigos:{}".format(socket.gethostname())
            print(mensagem)
            while True:
                broadcast_socket.sendto(mensagem.encode(), (ip_broadcast, porta_broadcast))
                time.sleep(5)  # Envia a mensagem de broadcast a cada 5 segundos

    # escuta por maquinas na rede
    def listen_for_broadcasts(self, ip_broadcast, porta_broadcast):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_ouvinte:
            socket_ouvinte.bind(("", porta_broadcast))
            while True:
                message, addr = socket_ouvinte.recvfrom(BUFFER_SIZE)
                if message.startswith(b"busca-se amigos:"):
                    discovered_nodes.add(addr)
                    print(f"Discovered node: {addr}")    
            
    def entra_na_rede(self):    
        
    # manda mensagem para alvo
    def manda_mensagem(self, alvo, operacao, mensagem):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((alvo.ip, porta))
        s.send(f"{operacao} {mensagem}".encode())
        s.close()
        
    # recebe mensagem e seleciona qual operacao fazer
    def escuta(self, porta):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', porta))
        s.listen(1000)
        conn, addr = s.accept()
        operacao, mensagem = conn.recv(1024).decode().split()
        conn.close()
        s.close()
        print(f"Operacao: {operacao}")
        print(f"Mensagem: {mensagem}")
        return operacao, mensagem
    # operacoes ate agora:
    # 1 - entra na rede
        # manda mensagem para todas as maquinas na rede 
        # (identificada atraves da porta)
    # 2 - nova maquina na rede
        # recebe mensagem de uma maquina que entrou na rede e 
        # insere o ip da maquina na lista de maquinas
    # 3 - inicia partida
    # 4 - distribui cartas e o vira
    # 5 - coleta palpites
    # 6 - bota carta na mesa
    # 7 - verifica quem ganhou a rodada, diminui pontos dos perdedores e incrementa cartas
    # 8 - encerra partida
     