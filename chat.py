# pip install crc8

import carta
import socket
import time
import json
import struct
import zlib
import jogador
import baralho
import verificador
import re

BUFFER_SIZE = 1024
BROADCAST_IP = "255.255.255.255"
BROADCAST_PORT = 44445
LOCAL_PORT = 44446  # Porta de escuta local
MAX_MACHINES = 2  # Número máximo de máquinas na rede

OPERATION_CODES = {
    "ACK": 0,
    "NACK": 1,
    "ORDENACAO": 2,
    "PALPITA": 3,
    "MOSTRAR": 4,
    "JOGAR": 5,
    "ENVIA_REDE": 6,
    "CONVITE": 7,
    "BUSCO AMIGOS": 8,
    "ESPERANDO AMIGOS": 9,
    "RECEBE CARTA": 10,
    "JOGAR CEGO": 11,
    "PALPITA CEGO": 12,
    "PERDEU": 13,
    "PERDI": 14,
    "OPERATION_16": 15,
    "ACK": 16,
    "NACK": 17,
}

REVERSE_OPERATION_CODES = {v: k for k, v in OPERATION_CODES.items()}


def eh_duplicado(lista, elemento):
    if elemento in lista:
        return True 
    return False


def create_message(origem_ip, destination_ip, operation, dados, acao):
    try:
        data_bytes = dados.encode('utf-8')
        data_length = len(data_bytes)

        # Ajustando a formatação da mensagem
        message_format = "20s 20s B H B"
        packed_message = struct.pack(message_format, origem_ip.encode('utf-8'), destination_ip.encode('utf-8'), operation, data_length, acao) + data_bytes

        # Calculando o CRC
        crc = zlib.crc32(packed_message)

        # Anexando o CRC à mensagem empacotada
        message_with_crc = packed_message + struct.pack("I", crc)
        
        return message_with_crc
    except Exception as e:
        print(f"Error creating message: {e}")
        raise

def parse_message(message):
    try:
        header_format = "20s 20s B H B"
        header_size = struct.calcsize(header_format)

        # Desempacotando o cabeçalho
        header = message[:header_size]
        data_length = struct.unpack(header_format, header)[3]

        # Desempacotando os dados
        dados = message[header_size:header_size + data_length]

        # Desempacotando o CRC recebido
        received_crc = struct.unpack("I", message[header_size + data_length:header_size + data_length + 4])[0]

        # Calculando o CRC a partir da mensagem recebida
        calculated_crc = zlib.crc32(header + dados)

        if calculated_crc != received_crc:
            raise ValueError("CRC check failed")

        origem_ip, destination_ip, operation, _, acao = struct.unpack(header_format, header)

        # Construindo o dicionário da mensagem
        message_dict = {
            'origem': origem_ip.decode('utf-8').strip('\x00'),
            'destino': destination_ip.decode('utf-8').strip('\x00'),
            'operacao': operation,
            'dados': dados.decode('utf-8'),
            'crc': received_crc,
            'acao': acao
        }

        return message_dict
    except Exception as e:
        print(f"Error parsing message: {e}")
        raise


class Maquina:
    def __init__(self):
        self.ip = self.pega_endereco_ip()
        self.prox_ip = None
        self.bastao = False
        self.estado = "INICIO"
        self.network_nodes = []  # Lista de máquinas na rede
        self.jogador = jogador.Jogador(self.ip)
        self.vira = None
        self.qnt_cartas = 1
        self.controladorPalpites = []
        self.controladorCartas = []
        
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
        mensagem_dict = parse_message(mensagem)
        print(f"mensagem recebida de {origem} -> {mensagem_dict['operacao']}: {mensagem_dict['dados']}")
        # acao == 0 todos podem ver a mensagem, tomar alguma acao interna e passar pra frente a mensagem inicial
        if mensagem_dict["acao"] == 0:
            if mensagem_dict["destino"] == BROADCAST_IP and self.bastao:
                # ADICIONA NOVA MAQUINA NA REDE
                if mensagem_dict["operacao"] == OPERATION_CODES["BUSCO AMIGOS"]:
                    print(f"Pedido de amizade recebido de {mensagem_dict['origem']}")
                    self.send_message(self.ip, origem, LOCAL_PORT, "ACK", f"recebido", 1)
                    time.sleep(1)
                    if self.send_message(self.ip, origem, LOCAL_PORT, "CONVITE", f"venha jogar comigo", 1) != 0:                
                        if not eh_duplicado(self.network_nodes, mensagem_dict["origem"]):
                            self.network_nodes.append(mensagem_dict["origem"])
                        return 1
            # ORGANIZA POSICOES NA REDE
            if mensagem_dict["operacao"] == OPERATION_CODES["ORDENACAO"]:
                self.send_message(self.ip, origem, LOCAL_PORT, "ACK", f"recebido", 1)
                string_aux = mensagem_dict["dados"].split("ANOTA: ")[1]
                self.network_nodes = string_aux.strip('[]').replace("'", "").split(', ')
                self.prox_ip = self.network_nodes[(self.network_nodes.index(self.ip) + 1) % len(self.network_nodes)]
                print()
                print(f"Proximo ip: {self.prox_ip}")
                self.encaminha_mensagem(mensagem)
                return 1   
            # MOSTRA CARTAS DOS JOGADORES 
            elif mensagem_dict["operacao"] == OPERATION_CODES["MOSTRAR"]:
                vira = json.loads(mensagem_dict["dados"])["vira"]
                print(f"Vira da rodada: {vira}")
                print(f"Cartas na minha mao: {self.jogador.mao}")
                if mensagem_dict["origem"] == self.ip:
                    return 1
                self.encaminha_mensagem(mensagem)          
                return 1
            # COLETA PALPITES DOS JOGADORES
            elif mensagem_dict["operacao"] == OPERATION_CODES["PALPITA"]:
                print("mensagem dentro do palpita", mensagem_dict["dados"])
                self.send_message(self.ip, origem, LOCAL_PORT, "ACK", f"recebido", 1)
                vira = json.loads(mensagem_dict["dados"])["vira"]
                qnt_cartas = json.loads(mensagem_dict["dados"])["qnt_cartas"]
                if qnt_cartas == 1:
                    print("as cegas")
                    
                    palpite = input("voce faz essa?")
                print(f"Vira da rodada: {vira}")
                print(self.jogador.mao)
                palpite = input("quantas rodadas voce faz?")
                # incrementa array de palpites
                mensagem_dict["dados"] = json.loads(mensagem_dict["dados"])
                mensagem_dict["dados"]["palpites"].append(palpite)
                # se a mensagem chegou ao final da rede (origem)
                if mensagem_dict["dados"]["destino"] == self.ip:
                    self.controladorPalpites = mensagem_dict["dados"]["palpites"]
                    print("palpites coletados!", self.controladorPalpites)
                    return 11
                # encaminha ate chegar na origem (onde o bastao esta)    
                self.encaminha_mensagem(
                    create_message(self.ip, mensagem_dict["destino"], 
                                   OPERATION_CODES["PALPITA"], 
                                   json.dumps(mensagem_dict["dados"]), 0)
                    )
                return 1
            # COLETA CARTAS DOS JOGADORES NAS CEGAS
            elif mensagem_dict["operacao"] == OPERATION_CODES["JOGAR CEGO"]:
                self.send_message(self.ip, origem, LOCAL_PORT, "ACK", f"recebido", 1)
                carta_jogada = self.jogador.mao.joga_carta(int(0))
                mensagem_dict["dados"] = json.loads(mensagem_dict["dados"])
                mensagem_dict["dados"]["cartas"].append({
                    "ip": self.ip, 
                    "carta": str(carta_jogada)
                    })
                if mensagem_dict["dados"]["destino"] == self.ip:
                    print("cartas coletadas!", mensagem_dict["dados"]["cartas"])
                    self.controladorCartas = mensagem_dict["dados"]["cartas"]
                    return 7
                self.encaminha_mensagem(
                    create_message(self.ip, mensagem_dict["destino"], OPERATION_CODES["JOGAR CEGO"], 
                                   json.dumps(mensagem_dict["dados"]), 0)
                    )
            # COLETA PALPITES MOSTRANDO A CARTA DOS ADVERSARIOS
            elif mensagem_dict["operacao"] == OPERATION_CODES["PALPITA CEGO"]:
                self.send_message(self.ip, origem, LOCAL_PORT, "ACK", f"recebido", 1)
                print("cartas dos adversarios")
                print("mensagem dentro do palpita", mensagem_dict["dados"])
                dados_formatados = json.loads(mensagem_dict["dados"])
                for item in dados_formatados["cartas"]:
                    if item["ip"] != self.ip:
                        print(f"{item['ip']} tem {item['carta']}")
                palpite = input("voce faz essa rodada?\n1 - sim\n2 - nao\n")
                # validacao da entrada
                bandeira = False
                while not bandeira:
                    if palpite == "1" or palpite == "2":
                        bandeira = True
                    else:
                        palpite = input("opcao invalida, digite 1 (para SIM) ou 2 (para NAO)\n")
                    
                mensagem_dict["dados"] = json.loads(mensagem_dict["dados"])
                mensagem_dict["dados"]["palpites"].append({"ip": self.ip, "palpite": palpite})
                # se a mensagem chegou ao final da rede (origem)
                if mensagem_dict["dados"]["destino"] == self.ip:
                    self.controladorPalpites = mensagem_dict["dados"]["palpites"]
                    print("palpites cegos coletados!", self.controladorPalpites)
                    return 8
                self.encaminha_mensagem(
                    create_message(self.ip, mensagem_dict["destino"], OPERATION_CODES["PALPITA CEGO"], 
                                   json.dumps(mensagem_dict["dados"]), 0)
                    )
                
            elif mensagem_dict["operacao"] == OPERATION_CODES["JOGAR"]:
                self.send_message(self.ip, origem, LOCAL_PORT, "ACK", f"recebido", 1)
                print("cartas na mao", self.jogador.mao)
                # exibe index de cada carta na tela 
                self.jogador.mao.imprime_mao()
                carta = input("qual carta voce quer jogar?")
                
                mensagem_dict["dados"] = json.loads(mensagem_dict["dados"])
                mensagem_dict["dados"]["cartas"].append(str(self.jogador.mao.joga_carta(int(carta))))
                if mensagem_dict["dados"]["destino"] == self.ip:
                    self.controladorCartas = mensagem_dict["dados"]["cartas"]
                    print("cartas coletadas!", self.controladorCartas)
                    return 6
                self.encaminha_mensagem(
                    create_message(self.ip, mensagem_dict["destino"], OPERATION_CODES["JOGAR"], 
                                   json.dumps(mensagem_dict["dados"]), 0)
                    )
        # acao == 1 so o destino faz algo e repassa a mensagem     
        elif mensagem_dict["acao"] == 1:
            if mensagem_dict["destino"] == self.ip:
                # RECEBIMENTO DO CONVITE PARA ENTRAR NA REDE
                if mensagem_dict["operacao"] == OPERATION_CODES["CONVITE"]:
                    print(f"Convite recebido de {mensagem_dict['origem']}")
                    self.send_message(self.ip, origem, LOCAL_PORT, "ACK", f"recebido", 1)
                    return 3
                # RECEBIMENTO DE CARTA
                elif mensagem_dict["operacao"] == OPERATION_CODES["RECEBE CARTA"]:
                    self.send_message(
                        mensagem_dict["origem"], self.prox_ip, 
                        LOCAL_PORT, "ACK", f"recebido", 1
                        )
                    carta = json.loads(mensagem_dict["dados"])["carta"]
                    self.jogador.mao.recebe_carta(carta)
                    return 1
                elif mensagem_dict["operacao"] == OPERATION_CODES["PERDEU"]:
                    self.send_message(self.ip, origem, LOCAL_PORT, "ACK", f"recebido", 1)
                    self.jogador.vidas -= 1
                    if self.jogador.vidas == 0:
                        print("voce perdeu o jogo!")
                        self.envia_mensagem_anel(self.ip, mensagem_dict["origem"], LOCAL_PORT, "PERDI", "perdi", 1)
                    return 1
                elif mensagem_dict["operacao"] == OPERATION_CODES["PERDI"]:
                    self.send_message(self.ip, origem, LOCAL_PORT, "ACK", f"recebido", 1)
                    self.network_nodes.remove(origem)
                    self.prox_ip = self.network_nodes[(self.network_nodes.index(self.ip) + 1) % len(self.network_nodes)]
                    # reorganiza a rede
                    self.envia_mensagem_anel(self.ip, self.prox_ip, LOCAL_PORT, "ORDENACAO", f"ANOTA: {str(self.network_nodes)}", 0)
                    # tratar caso em que quem perdeu é o cara com bastao
                    return 1
            else:
                # MENSAGEM VOLTOU PARA O COMECO DA REDE
                if mensagem_dict["origem"] == self.ip:
                    return 1
                # MENSAGEM NAO CHEGOU NO DESTINO AINDA
                self.encaminha_mensagem(mensagem)
                return 1
    
    def encaminha_mensagem(self, mensagem):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
            send_socket.sendto(mensagem, (self.prox_ip, LOCAL_PORT))
            print(f"mensagem encaminhada para {self.prox_ip}:{LOCAL_PORT}")             
            print()           
                          
    # pede pra entrar na rede
    def avisa_elas_broadcast(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_socket:
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = f"BUSCO AMIGOS: sou o {self.ip}"
            for _ in range(2):  # Tenta 5x
                print("buscando alguem na rede")
                message = { 
                    "acao": 0, "origem": self.ip, 
                    "destino": BROADCAST_IP, 
                    "operacao": "BUSCO AMIGOS", 
                    "dados": f"sou o {self.ip}"
                }
                message = create_message(self.ip, BROADCAST_IP, 
                                         OPERATION_CODES["BUSCO AMIGOS"], 
                                         f"sou o {self.ip}", 0)
                # faz o broadcast
                broadcast_socket.sendto(message, (BROADCAST_IP, BROADCAST_PORT))
                # espera 2s pra ver se alguem responde
                mensagem, origem = self.escuta_temporizado(LOCAL_PORT, 2) # self.escuta_mensagens(True)
                if mensagem != None:
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

    def send_message(self, ip_origem: str, ip_destino: str, porta: int, operacao: str, dados: str, acao: int):
        # busca no dicionario de operacoes qual o numero dessa operacao
        operation_code = OPERATION_CODES[operacao]
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
            # codifica mensagem
            message = create_message(ip_origem, ip_destino, operation_code, dados, acao)
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

    def envia_mensagem_anel(self, ip_origem: str, ip_destino: str, porta: int, operacao: str, dados: str, acao: int):                
        operation_code = OPERATION_CODES[operacao]
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
            message = create_message(ip_origem, ip_destino, operation_code, dados, acao)
            send_socket.sendto(message, (self.prox_ip, porta))
            print()
            print(f"mensagem enviada para {self.prox_ip}:{porta} -> {operacao}: {dados}")
            print("operacao", operacao)
            print("dados", dados)
            print()
            tempo = 3
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
            listen_socket.bind(("", porta))
            listen_socket.settimeout(tempo)
            try:
                print("esperando ACK/NACK")
                ack_message, _ = listen_socket.recvfrom(BUFFER_SIZE)
                retorno = self.trata_mensagens(ack_message, ip_destino)
                if retorno == 2:
                    return 1
                # um retorno pra cada tipo de verificacao que a maquina tem que fazer:
                # resultado dos palpites
                # resultado das cartas jogadas
                # resultado do vencedor da rodada 
                # resultado do vencedor do jogo (desse carteado) 
                #   (anuncia quem ganhou e diminui os pontos da galera)
                #           caso quem esta com o bastao tenha perdido, envia uma mensagem pro proximo
                #         avisando que ele precisa ser retirado antes da entrega das cartas
                
                # passa bastao pro proximo
            except socket.timeout:
                print(f"nenhum ACK/NACK recebido nos ultimos {tempo}s")
                return 0
            
    
    def escuta_mensagens(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
            listen_socket.bind(("", LOCAL_PORT))
            while True:
                message, addr = listen_socket.recvfrom(BUFFER_SIZE)
                try:
                    resultado = self.trata_mensagens(message, addr[0])
                    print(self.estado)
                    if resultado == 11:
                        self.estado = "PEGA CARTAS"
                        break
                    elif resultado == 12:
                        print("mudou de estado")
                        self.estado = "VERIFICANDO"
                        break
                    elif resultado == 7:
                        self.estado = "PEGA PALPITES CEGO"
                        break
                    elif resultado == 8:
                        self.estado = "VERIFICA 1a RODADA"
                        print("mudou de estado", self.estado)
                        break
                except ValueError as e:
                    print(f"Error parsing message: {e}")
                    # Send NACK
                    nack_message = create_message(addr[0], OPERATION_CODES["NACK"], "NACK")
                    listen_socket.sendto(nack_message, addr)

def main():
    #nome = input("Qual o nome da máquina? ")
    instancia = Maquina()	
    print(f"esta maquina está com IP {instancia.ip}")
    qnt_cartas = 1
    
    # estados = {inicio, pega cartas 1a rodada, pega palpites 1a rodada e verifica}
    # estados = {inicio, pega palpites, pega cartas e verifica}
    
    # estados = {inicio, distribuindo, ouvindo palpites, 
        #   aguardando, jogando, verificando ganhador}

    if instancia.avisa_elas_broadcast() == 0: 
        print("Sou o primeiro da rede!")
        instancia.bastao = True
        instancia.network_nodes.append(instancia.ip)
        instancia.estado = "INICIO"
        # ENQUANTO NAO TIVER TODAS AS MAQUINAS NA REDE TEM QUE OUVIR NA PORTA DE BROADCAST
        print("Aguardando outras máquinas pedirem pra entrar no jogo...")
        instancia.escuta_broadcast()
        
        # 2 segundos pra garantir que todas as maquinas estao prontas pra ouvir 
        time.sleep(2)
        meu_index = instancia.network_nodes.index(instancia.ip)
        instancia.prox_ip = instancia.network_nodes[(meu_index + 1) % len(instancia.network_nodes)]
        # avisa como está a distribuicao do anel
        for maquina in instancia.network_nodes:
           if maquina != instancia.ip:
                instancia.envia_mensagem_anel(instancia.ip, maquina, LOCAL_PORT, 
                                              "ORDENACAO", f"ANOTA: {str(instancia.network_nodes)}", 0)
                #instancia.send_message(instancia.ip, maquina, LOCAL_PORT, "ORDENACAO", f"ANOTA: {str(instancia.network_nodes)}")
        instancia.prox_ip = instancia.network_nodes[(instancia.network_nodes.index(instancia.ip) + 1) % len(instancia.network_nodes)]
        print("todas as maquinas foram informadas!")
            
    # inicia jogo
    print("Estou esperando/ouvindo na rede.")
    while True:
        if instancia.bastao:
            if instancia.estado == "INICIO":
                print("Agora é a minha vez de operar a rede!")
                monte_cartas = baralho.Baralho()
                monte_cartas.embaralhar()
                
                # distribui cartas
                meu_index = instancia.network_nodes.index(instancia.ip)
                for i in range(qnt_cartas):
                    for j in range(1, len(instancia.network_nodes)):
                        index_atual = (meu_index + j) % len(instancia.network_nodes)
                        print("index", index_atual)
                        # acao == 0 todos fazem algo, provavelmente interno, e repassam a mensagem
                        # acao == 1 só o destino faz algo e repassa a mensagem
                        mensagem = {"acao": 1, "destino": instancia.network_nodes[index_atual], 
                                        "carta": str(monte_cartas.entrega_carta())}
                        instancia.envia_mensagem_anel(instancia.ip, instancia.network_nodes[index_atual], 
                                                      LOCAL_PORT, "RECEBE CARTA", f"{json.dumps(mensagem)}", 1)
                    instancia.jogador.mao.recebe_carta(monte_cartas.entrega_carta())
                instancia.vira = monte_cartas.entrega_carta()
                print("Cartas distribuídas!")
                
                if instancia.qnt_cartas == 1 and instancia.estado == "INICIO":
                    # TROCA ESTADO
                    instancia.estado = "PEGA CARTAS CEGO"
                # mostrando cartas
                message = {"acao": 0, "origem": instancia.ip, "destino": 
                                instancia.ip, "vira": str(instancia.vira)}
                instancia.envia_mensagem_anel(instancia.ip, instancia.ip, LOCAL_PORT, 
                                              "MOSTRAR", json.dumps(message), 0)

            # PRIMEIRA RODADA
            if instancia.qnt_cartas == 1:
                if instancia.estado == "PEGA CARTAS CEGO":
                    # COLETA CARTAS AS CEGAS
                    for j in range(1, len(instancia.network_nodes)):
                        index_atual = (meu_index + j) % len(instancia.network_nodes)
                        mensagem = {
                            "acao": 0, "origem": instancia.ip, 
                            "destino": instancia.ip, "cartas": [], 
                            "vira": str(instancia.vira), "posicao": index_atual,
                            "qnt_cartas": qnt_cartas
                            }
                        instancia.envia_mensagem_anel(instancia.ip, maquina, LOCAL_PORT, 
                                                        "JOGAR CEGO", json.dumps(mensagem), 0)  

                elif instancia.estado == "PEGA PALPITES CEGO":
                    # COLEGA PALPITE MOSTRANDO A CARTA DOS ADVERSARIOS
                    for j in range(1, len(instancia.network_nodes)):
                        index_atual = (meu_index + j) % len(instancia.network_nodes)
                        mensagem = {
                            "acao": 1, "origem": instancia.ip, 
                            "destino": instancia.ip, "palpites": [], 
                            "vira": str(instancia.vira), "posicao": index_atual,
                            "qnt_cartas": qnt_cartas, "cartas": instancia.controladorCartas
                            }
                        instancia.envia_mensagem_anel(instancia.ip, maquina, LOCAL_PORT, 
                                                    "PALPITA CEGO", json.dumps(mensagem), 0)    
                elif instancia.estado == "VERIFICA 1a RODADA":
                    # MOSTRAR O VIRA PRA GALERA e qual carta cada um jogou
                    print("verificando 1a rodada")
                    print(instancia.controladorPalpites)
                    print(instancia.controladorCartas)
                    instancia_verificadora = verificador.Verificador()
                    
                    for item in instancia.controladorCartas:
                        print(item)
                        carta_num = item["carta"][0]
                        naipe = re.search(r'de\s+(.*)', item["carta"]).group(1)
                        print("carta_num", carta_num, "naipe", naipe)
                        instancia_carta = carta.Carta(carta_num, naipe)
                        instancia_verificadora.bota_carta_na_mesa_com_manilha(
                            instancia_carta, item["ip"], instancia.vira
                            )
                    for item in instancia.controladorPalpites:
                        if str(instancia_verificadora) == "Embuchou!":
                            # envia mensagem de penalidade pra quem errou o palpite
                            if item["palpite"] == "1":
                                mensagem = {
                                    "acao": 1, "origem": instancia.ip,
                                    "destino": item["ip"], "vira": str(instancia.vira),
                                    "posicao": item["ip"], "penalidade": 1
                                }
                                instancia.envia_mensagem_anel(
                                    instancia.ip, item["ip"], LOCAL_PORT, 
                                    "PERDEU", json.dumps(mensagem), 1
                                    )
                        elif re.match(r"(.*?) fez", str(instancia_verificadora)).group(1) == item["ip"]:
                            if item["palpite"] == "1":
                                # COLOCAR MENSAGEM DE NAO PERDER
                                pass
                            # verificar se isso aqui atende ao caso: falei que nao ia fazer e fiz
                            else:
                                instancia.envia_mensagem_anel(
                                    instancia.ip, item["ip"], LOCAL_PORT, 
                                    "PERDEU", json.dumps(mensagem), 1
                                    )
                    print(instancia_verificadora)
                        # incrementa quantidade de cartas (do proximo) e passa bastao pro proximo
                        
                    
                    pass
                else:
                    pass
                #for j in range(1, len(instancia.network_nodes)):
                #    index_atual = (meu_index + j) % len(instancia.network_nodes)
                #    mensagem = {
                #        "acao": 1, "origem": instancia.ip, 
                #        "destino": instancia.ip, "palpites": [], 
                #        "vira": str(instancia.vira), "posicao": index_atual,
                #        "qnt_cartas": qnt_cartas
                #        }
                #    instancia.envia_mensagem_anel(instancia.ip, maquina, LOCAL_PORT, 
                #                                   "PALPITA", json.dumps(mensagem), 0)    
           
            #elif instancia.estado == "PEGA CARTAS":    
                # COLETA CARTAS
            #    for j in range(1, len(instancia.network_nodes)):
            #        index_atual = (meu_index + j) % len(instancia.network_nodes)
            #        mensagem = {
            #            "acao": 0, "origem": instancia.ip, 
            #            "destino": instancia.ip, "cartas": [], 
            #            "vira": str(instancia.vira), "posicao": index_atual,
            #            "qnt_cartas": qnt_cartas
            #            }
            #        instancia.envia_mensagem_anel(instancia.ip, maquina, LOCAL_PORT, 
            #                                        "JOGAR", json.dumps(mensagem), 0)    
                    
            elif instancia.estado == "VERIFICANDO":
                pass
            # entregar cartas
            # coletar palpites
            # passa bastao pro proximo
            # proximo joga carta
            # passa mensagem pra jogar carta

        instancia.escuta_mensagens()   

if __name__ == "__main__":    
    main()