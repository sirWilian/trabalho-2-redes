# pip install crc8

import socket
import time
import json
import struct
import zlib
import jogador
import baralho

BUFFER_SIZE = 1024
BROADCAST_IP = "255.255.255.255"
BROADCAST_PORT = 44445
LOCAL_PORT = 44446  # Porta de escuta local
MAX_MACHINES = 3  # Número máximo de máquinas na rede

OPERATION_CODES = {
    "ACK": 0,
    "NACK": 1,
    "ORDENACAO": 2,
    "COLETAR_PALPITES": 3,
    "JOGA_CARTA": 4,
    "VERIFICA_GANHADOR_RODADA": 5,
    "ENVIA_REDE": 6,
    "CONVITE": 7,
    "BUSCO AMIGOS": 8,
    "ESPERANDO AMIGOS": 9,
    "RECEBE CARTA": 10,
    "OPERATION_12": 11,
    "OPERATION_13": 12,
    "OPERATION_14": 13,
    "OPERATION_15": 14,
    "OPERATION_16": 15,
    "ACK": 16,
    "NACK": 17,
}

REVERSE_OPERATION_CODES = {v: k for k, v in OPERATION_CODES.items()}


def eh_duplicado(lista, elemento):
    if elemento in lista:
        return True 
    return False

def create_message(destination_ip, operation, dados):
    data_bytes = dados.encode('utf-8')
    data_length = len(data_bytes)
    
    message_format = "20s B H"
    packed_message = struct.pack(message_format, destination_ip.encode('utf-8'), operation, data_length) + data_bytes
    
    crc = zlib.crc32(packed_message)
    message_with_crc = packed_message + struct.pack("I", crc)
    
    return message_with_crc

def parse_message(message):
    header_format = "20s B H"
    header_size = struct.calcsize(header_format)
    
    header = message[:header_size]
    data_length = struct.unpack(header_format, header)[2]
    dados = message[header_size:header_size + data_length]
    received_crc = struct.unpack("I", message[header_size + data_length:])[0]
    
    calculated_crc = zlib.crc32(header + dados)
    
    if calculated_crc != received_crc:
        raise ValueError("CRC check failed")
    
    destination_ip, operation, _ = struct.unpack(header_format, header)
    
    return destination_ip.decode('utf-8').strip('\x00'), operation, dados.decode('utf-8')

class Maquina:
    def __init__(self):
        self.ip = self.pega_endereco_ip()
        self.prox_ip = None
        self.bastao = False
        self.network_nodes = []  # Lista de máquinas na rede
        self.jogador = jogador.Jogador(self.ip)
    
    def pega_endereco_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
            return local_ip
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def escuta_temporizado(self, porta: int, tempo: int):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
            listen_socket.bind(("", porta))
            listen_socket.settimeout(tempo)
            try:
                message, addr = listen_socket.recvfrom(BUFFER_SIZE)
                return message, addr[0]
            except socket.timeout:
                return None, None
          
    def trata_mensagens(self, mensagem: str, origem: str):
        destino, operacao, dados = parse_message(mensagem)
        print(destino, operacao, dados)
        if destino == self.ip:
            if operacao == OPERATION_CODES["CONVITE"]:
                print(f"Convite recebido de {origem}")
                self.send_message(origem, LOCAL_PORT, "ACK", f"recebido")
                # quase pronta pra partida
                return 3    
            elif operacao == OPERATION_CODES["ACK"]:
                print(f"ACK recebido de {origem}")
                return 2
            elif operacao == OPERATION_CODES["ORDENACAO"]:
                print('recebi a ordem das maquinas')
                self.send_message(origem, LOCAL_PORT, "ACK", f"recebido")
                # faz o parse da string array 
                string_aux = dados.split("ANOTA: ")[1]
                self.network_nodes = string_aux.strip('[]').replace("'", "").split(', ')
                # atualiza o proximo ip
                self.prox_ip = self.network_nodes[(self.network_nodes.index(self.ip) + 1) % len(self.network_nodes)]
                return 1
            elif operacao == OPERATION_CODES["RECEBE CARTA"]:
                dados = json.loads(dados)
                print('hahahahaha')
                if dados["destino"] == self.ip:
                    self.send_message(origem, LOCAL_PORT, "ACK", f"recebido")
                    carta = dados["carta"]
                    self.jogador.mao.recebe_carta(carta)
                    print(f"Carta {carta} recebida e adicionada à mão.")
                    return 1
                else:
                    return 4
                    self.send_message(self.prox_ip, LOCAL_PORT, "RECEBE CARTA", f"{json.dumps(dados)}")    
                    
                self.jogador.mao.process_message(dados)
                print(f"Carta recebida de {origem}")
                print(self.jogador.mao)
                self.send_message(origem, LOCAL_PORT, "ACK", f"recebido")
                return 1
            
        # se a mensagem for para broadcast e o bastao estiver com a maquina
        elif destino == BROADCAST_IP and self.bastao:
            if operacao == OPERATION_CODES["BUSCO AMIGOS"]:
                print(f"Pedido de amizade recebido de {origem}")
                self.send_message(origem, LOCAL_PORT, "ACK", f"recebido")
                time.sleep(1)
                if self.send_message(origem, LOCAL_PORT, "CONVITE", f"venha jogar comigo") != 0:                
                    if not eh_duplicado(self.network_nodes, origem):
                        self.network_nodes.append(origem)
                        print(f"Adicionando {origem} à rede")
                        print("estado atual da rede", self.network_nodes)
                    return 1
          
    # pede pra entrar na rede
    def avisa_elas_broadcast(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_socket:
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = f"BUSCO AMIGOS: sou o {self.ip}"
            for _ in range(2):  # Tenta 5x
                print("buscando alguem na rede")
                message = create_message(BROADCAST_IP, OPERATION_CODES["BUSCO AMIGOS"], f"sou o {self.ip}")
                # faz o broadcast
                broadcast_socket.sendto(message, (BROADCAST_IP, BROADCAST_PORT))
                # espera 2s pra ver se alguem responde
                mensagem, origem = self.escuta_temporizado(LOCAL_PORT, 2) # self.escuta_mensagens(True)
                if mensagem != None:
                    # esse ACK/NACK eh feito na mao devido a diferenca de portas na hora de enviar a primeira mensagem
                    self.trata_mensagens(mensagem, origem)
                    # agora espera pelo convite
                    while True:
                        mensagem, origem = self.escuta_temporizado(LOCAL_PORT, 5)
                        if mensagem != None: # alguem respondeu
                            return self.trata_mensagens(mensagem, origem)
                time.sleep(1)
                
            # sozinho na rede
            return 0

    def escuta_broadcast(self):
        while len(self.network_nodes) < MAX_MACHINES:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
                listen_socket.bind(("", BROADCAST_PORT))
                while len(self.network_nodes) < MAX_MACHINES:
                    message, addr = listen_socket.recvfrom(BUFFER_SIZE)
                    try:
                        self.trata_mensagens(message, addr[0])
                    except ValueError as e:
                        print(f"Error parsing message: {e}")                 
                        # Send NACK
                        nack_message = create_message(addr[0], OPERATION_CODES["NACK"], "NACK")
                        listen_socket.sendto(nack_message, addr)

    def send_message(self, ip_destino: str, porta: int, operacao: str, dados: str):
        # busca no dicionario de operacoes qual o numero dessa operacao
        operation_code = OPERATION_CODES[operacao]
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
            # codifica mensagem
            message = create_message(ip_destino, operation_code, dados)
            # envia mensagem
            send_socket.sendto(message, (ip_destino, porta))
            print(f"mensagem enviada para {ip_destino}:{porta} -> {operacao}: {dados}")
            
            # ACK não precisa esperar ACK
            if operation_code == OPERATION_CODES["ACK"]:
                return -1
            tempo = 3
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
            listen_socket.bind(("", porta))
            listen_socket.settimeout(tempo)  # Timeout para esperar ACK/NACK
            try:
                print("esperando ACK/NACK")
                ack_message, _ = listen_socket.recvfrom(BUFFER_SIZE)
                
                if self.trata_mensagens(ack_message, ip_destino) == 2:
                    return 1

            except socket.timeout:
                print(f"nenhum ACK/NACK recebido nos ultimos {tempo}s")
                return 0
                
    def escuta_mensagens(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
            listen_socket.bind(("", LOCAL_PORT))
            while True:
                message, addr = listen_socket.recvfrom(BUFFER_SIZE)
                try:
                    if self.trata_mensagens(message, addr[0]) == 4: # nao eh a maq certa
                        print("nao eh a certa")
                        listen_socket.sendto(message, (self.prox_ip, LOCAL_PORT))
                except ValueError as e:
                    print(f"Error parsing message: {e}")
                    
                    # Send NACK
                    nack_message = create_message(addr[0], OPERATION_CODES["NACK"], "NACK")
                    listen_socket.sendto(nack_message, addr)

def main():
    #nome = input("Qual o nome da máquina? ")
    instancia = Maquina()	
    print(f"esta maquina está com IP {instancia.ip}")
    estado = "INICIO"
    qnt_cartas = 1
    
    # estados = {inicio, distribuindo, ouvindo palpites, 
        #   aguardando, jogando, verificando ganhador}

    if instancia.avisa_elas_broadcast() == 0: 
        print("Sou o primeiro da rede!")
        instancia.bastao = True
        instancia.network_nodes.append(instancia.ip)
        # ENQUANTO NAO TIVER TODAS AS MAQUINAS NA REDE TEM QUE OUVIR NA PORTA DE BROADCAST
        print("Aguardando outras máquinas pedirem pra entrar no jogo...")
        instancia.escuta_broadcast()
        
        # 5 segundos pra garantir que todas as maquinas estao prontas pra ouvir 
        time.sleep(5)
        # avisa como está a distribuicao do anel
        for maquina in instancia.network_nodes:
           if maquina != instancia.ip:
                instancia.send_message(maquina, LOCAL_PORT, "ORDENACAO", f"ANOTA: {str(instancia.network_nodes)}")
        instancia.prox_ip = instancia.network_nodes[(instancia.network_nodes.index(instancia.ip) + 1) % len(instancia.network_nodes)]
        print("todas as maquinas foram informadas!")
        
    # inicia jogo
    print("Estou esperando/ouvindo na rede.")
    while True:
        if instancia.bastao:
            if estado == "INICIO":
                print("Agora é a minha vez de operar a rede!")
                monte_cartas = baralho.Baralho()
                monte_cartas.embaralhar()
                
                # distribui cartas
                meu_index = instancia.network_nodes.index(instancia.ip)
                for i in range(qnt_cartas):
                    for j in range(1, len(instancia.network_nodes)):
                        index_atual = (meu_index + j) % len(instancia.network_nodes)
                        mensagem = {"destino": instancia.network_nodes[index_atual], "carta": str(monte_cartas.entrega_carta())}
                        instancia.send_message(instancia.prox_ip, LOCAL_PORT, "RECEBE CARTA", f"{json.dumps(mensagem)}")
                    instancia.jogador.mao.recebe_carta(monte_cartas.entrega_carta())



                # coleta palpites
                for maquina in instancia.network_nodes:
                    if maquina == instancia.ip:
                        palpite = input("Digite seu palpite: ")
                        continue
                    instancia.send_message(maquina, LOCAL_PORT, "COLETAR_PALPITES", f"palpite")    
            # entregar cartas
            # coletar palpites
            # passa bastao pro proximo
            # proximo joga carta
            # passa mensagem pra jogar carta
        instancia.escuta_mensagens()   

if __name__ == "__main__":
    
    main()
