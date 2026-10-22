import socket
import threading

class TCPServer:
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port
        self.server_socket = None
    
    def start_server(self):
        self.server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server listening on http://{self.host}:{self.port}")

        
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"Connection from {client_address}")

                client_thread = threading.Thread(
                    target = self._handle_client,
                    args = (client_socket, client_address),
                )
                client_thread.start()


            except OSError as exc:
                print(f"Accept failed {exc}")
                break

       
    def _handle_client(self, client_socket, client_address):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"Received: {data.decode()}")
        finally:
            client_socket.close()
            print(f"Disconnected from {client_address}")



if __name__ == "__main__":
    print("Starting up server...")
    server = TCPServer()
    server.start_server()



    
