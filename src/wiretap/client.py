import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('127.0.0.1', 8000)
client_socket.connect(server_address)

try:
    message = b"Hello, from wiretap!"
    client_socket.sendall(message)
    
    response = client_socket.recv(1024)
    print("Received from server:", response.decode())
finally:
    client_socket.close()

