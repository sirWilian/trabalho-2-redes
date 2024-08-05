import socket
import threading
import time

BROADCAST_IP = "255.255.255.255"
BROADCAST_PORT = 44445
LOCAL_PORT = 44446  # Porta de escuta local diferente da de broadcast
BUFFER_SIZE = 1024

# Lista de máquinas descobertas
discovered_nodes = set()

def broadcast_presence():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as broadcast_socket:
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = "DISCOVER:{}".format(socket.gethostname())
        while True:
            broadcast_socket.sendto(message.encode(), (BROADCAST_IP, BROADCAST_PORT))
            time.sleep(5)  # Envia a mensagem de broadcast a cada 5 segundos

def listen_for_broadcasts():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
        listen_socket.bind(("", BROADCAST_PORT))
        while True:
            message, addr = listen_socket.recvfrom(BUFFER_SIZE)
            if message.startswith(b"DISCOVER:"):
                discovered_nodes.add(addr)
                print(f"Discovered node: {addr}")

def listen_for_direct_messages():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
        listen_socket.bind(("", LOCAL_PORT))
        while True:
            message, addr = listen_socket.recvfrom(BUFFER_SIZE)
            print(f"Received message: {message.decode()} from {addr}")

def send_direct_message():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
        while True:
            message = input("Enter message to send: ")
            for node in discovered_nodes:
                send_socket.sendto(message.encode(), (node[0], LOCAL_PORT))
                print(f"Message sent to {node[0]}:{LOCAL_PORT}")

def main():
    # Thread para escutar mensagens de broadcast
    broadcast_thread = threading.Thread(target=listen_for_broadcasts)
    broadcast_thread.daemon = True
    broadcast_thread.start()

    # Thread para escutar mensagens diretas
    #direct_listen_thread = threading.Thread(target=listen_for_direct_messages)
    #direct_listen_thread.daemon = True
    #direct_listen_thread.start()

    # Thread para enviar presença via broadcast
    presence_thread = threading.Thread(target=broadcast_presence)
    presence_thread.daemon = True
    presence_thread.start()

    # Enviar mensagens diretas
    send_direct_message()

if __name__ == "__main__":
    main()

