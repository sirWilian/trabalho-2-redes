import socket
import threading
import time

BUFFER_SIZE = 1024
BROADCAST_IP = "255.255.255.255"
BROADCAST_PORT = 44445
LOCAL_PORT = 44446  # Porta de escuta local
MAX_MACHINES = 4  # Número máximo de máquinas na rede

class Maquina:
    def __init__(self, nome):
        self.nome = nome
        self.ip = self.pega_endereco_ip()
        self.prox_ip = None
        self.bastao = False
        self.stop_event = threading.Event()
        self.network_nodes = []  # Lista de máquinas na rede
    
    def pega_endereco_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
            return local_ip
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def broadcast_presence(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_socket:
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            message = f"BUSCO AMIGOS:{self.ip}"
            while not self.stop_event.is_set():
                broadcast_socket.sendto(message.encode(), (BROADCAST_IP, BROADCAST_PORT))
                print("Broadcast de presença enviado.")
                time.sleep(5)  # Envia a mensagem de broadcast a cada 5 segundos
                if len(self.network_nodes) >= MAX_MACHINES:
                    print("Número máximo de máquinas atingido. Parando broadcast.")
                    break
    
    def listen_for_broadcasts(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
            listen_socket.bind(("", BROADCAST_PORT))
            listen_socket.settimeout(10)  # Espera por respostas por 10 segundos
            try:
                while not self.stop_event.is_set():
                    message, addr = listen_socket.recvfrom(BUFFER_SIZE)
                    if addr[0] != self.ip:
                        print(f"Received message: {message.decode()} from {addr[0]}")
                        if message.decode().startswith("BUSCO AMIGOS:"):
                            response = f"JOIN:{self.ip}"
                            listen_socket.sendto(response.encode(), addr)
                        elif message.decode().startswith("JOIN:"):
                            if addr[0] not in self.network_nodes:
                                self.network_nodes.append(addr[0])
                                self.prox_ip = self.network_nodes[0] if self.prox_ip is None else self.network_nodes[self.network_nodes.index(self.prox_ip) + 1]
                                print(f"Ingressou na rede. Próximo IP: {self.prox_ip}")
                                # Informar a máquina que ela foi adicionada à rede
                                confirmation_message = "CONFIRMADO"
                                listen_socket.sendto(confirmation_message.encode(), addr)
                            if len(self.network_nodes) >= MAX_MACHINES:
                                self.stop_event.set()
                                print("Parando recepção de broadcast.")
                            break
            except socket.timeout:
                print("Nenhuma resposta recebida. Inicializando rede...")
                self.bastao = True
                self.network_nodes.append(self.ip)
    
    def send_message(self, message):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
            if self.prox_ip:
                send_socket.sendto(message.encode(), (self.prox_ip, LOCAL_PORT))
                print(f"Message sent to {self.prox_ip}:{LOCAL_PORT}")
    
    def listen_for_messages(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
            listen_socket.bind((self.ip, LOCAL_PORT))
            while not self.stop_event.is_set():
                message, addr = listen_socket.recvfrom(BUFFER_SIZE)
                if message:
                    print(f"Received message: {message.decode()} from {addr}")
                    if message.decode() == "TOKEN":
                        self.bastao = True
                        # Process and pass the token if needed
                        user_input = input("Enter message to send (or 'pass' to pass token): ")
                        if user_input.lower() == "pass":
                            self.bastao = False
                            self.send_message("TOKEN")
                        else:
                            self.send_message(user_input)
                    elif message.decode() == "CONFIRMADO":
                        self.stop_event.set()
                        print("Ingressou na rede. Parando broadcast de presença.")
                    else:
                        self.send_message(message.decode())
    
    def stop(self):
        self.stop_event.set()

def main():
    nome = input("Qual o nome da máquina? ")
    instancia = Maquina(nome)
    print(f"{nome} está com IP {instancia.ip}")

    # Thread para escutar mensagens de broadcast
    broadcast_thread = threading.Thread(target=instancia.listen_for_broadcasts)
    broadcast_thread.start()

    # Enviar broadcast de presença
    presence_thread = threading.Thread(target=instancia.broadcast_presence)
    presence_thread.start()

    # Thread para escutar mensagens
    listen_thread = threading.Thread(target=instancia.listen_for_messages)
    listen_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        instancia.stop()
        broadcast_thread.join()
        presence_thread.join()
        listen_thread.join()

if __name__ == "__main__":
    main()
