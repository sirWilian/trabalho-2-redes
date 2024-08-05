import jogador
import socket
import threading
import time


# i30 10.254.224.57
# i32 10.254.224.59 

BUFFER_SIZE = 1024
BROADCAST_IP = "255.255.255.255"
BROADCAST_PORT = 44445
LOCAL_PORT = 44446  # Porta de escuta local diferente da de broadcast

discovered_nodes = set()

class Maquina:
    def __init__(self, nome):
        self.ip = self.pega_endereco_ip()
        self.jogador = jogador.Jogador(nome) 
        # ip da proxima maquina. deve ser preenchido apos uma 
        # maquina entrar na rede. As maquinas entram na rede 
        # executando o programa e mandando uma mensagem na rede.
        # caso houver maquinas na rede. uma dessas maquinas deve verificar
        # o conjunto de maquinas, indicar qual posicao essa nova maquina assumirá,
        # indicar qual sera o ip da proxima maquina dela e incrementar o conjunto de maqs.
        self.prox = None 
        self.amigos = None
        self.bastao = False
    
    # ip da propria maquina na rede
    def pega_endereco_ip(self):
        try:
            # Cria um socket e conecta a um endereço externo para descobrir o IP local
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))  # Conecta a um servidor externo (Google DNS)
                local_ip = s.getsockname()[0]  # Obtém o IP local
            return local_ip
        except Exception as e:
            print(f"Error: {e}")
            return None
        
    # procura por maquinas na rede
    def broadcast_presence(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_socket:
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = "BUSCO AMIGOS:{}".format(socket.gethostname())
            while True:
                broadcast_socket.sendto(message.encode(), (BROADCAST_IP, BROADCAST_PORT))
                time.sleep(10)  # Envia a mensagem de broadcast a cada 5 segundos
        
    # escuta por maquinas na rede
    def listen_for_broadcasts(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
            listen_socket.bind(("", BROADCAST_PORT))
            while True:
                message, addr = listen_socket.recvfrom(BUFFER_SIZE)
                if message.startswith(b"BUSCO AMIGOS:") and addr[0] != self.ip:
                    discovered_nodes.add(addr[0])
                    print(f"Discovered node: {addr[0]}")
                
    def send_direct_message(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
            while True:
                message = input("Enter message to send: ")
                for node in discovered_nodes:
                    send_socket.sendto(message.encode(), (node, LOCAL_PORT))
                    print(f"Message sent to {node}:{LOCAL_PORT}")
                
    def listen_for_direct_messages(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
            listen_socket.bind(("", LOCAL_PORT))
            while True:
                message, addr = listen_socket.recvfrom(BUFFER_SIZE)
                print(f"Received message: {message.decode()} from {addr}")




def main():
    instancia = Maquina("Jogador")
    print(instancia.ip)
    # Thread para escutar mensagens de broadcast
    broadcast_thread = threading.Thread(target=instancia.listen_for_broadcasts)
    broadcast_thread.daemon = True
    broadcast_thread.start()

    # Thread para enviar presença via broadcast
    presence_thread = threading.Thread(target=instancia.broadcast_presence)
    presence_thread.daemon = True
    presence_thread.start()

    # Thread para escutar mensagens diretas
    direct_listen_thread = threading.Thread(target=instancia.listen_for_direct_messages)
    direct_listen_thread.daemon = True
    direct_listen_thread.start()
    
    # Enviar mensagens diretas
    instancia.send_direct_message()

    while True:
        if instancia.bastao:
            

if __name__ == "__main__":
    main()         
    #def entra_na_rede(self):    
        
    # manda mensagem para alvo
        
    # recebe mensagem e seleciona qual operacao fazer

    
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

