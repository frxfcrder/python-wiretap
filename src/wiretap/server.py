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
        buffer = b""

        while b"\r\n\r\n" not in buffer:
            data = client_socket.recv(1024)
            if not data:
                return
            buffer += data

        print(buffer.decode("utf-8"))
        
        

        header_section, separator, body = buffer.partition(b"\r\n\r\n")

        print("RAW BUFFER:", repr(buffer))
        print("BODY BYTES:", repr(body))
        print("BODY LENGTH:", len(body))

        
        header_lines = header_section.split(b"\r\n")
        

        request_line= header_lines[0].decode("utf-8")
        method, target, version = request_line.split()

        headers = {}

        for line in header_lines[1:]:
            line = line.decode("utf-8")

            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
                content_length = int(headers.get("content-length", 0))
                remaining = content_length - len(body)
                print(f"Body bytes received: {len(body)}")
                print(f"Body bytes remaining: {remaining}")

        print("PARSED HEADERS:")
        print(headers)

        print(f"Method: {method}")
        print(f"Target: {target}")
        print(f"Version: {version}")

        print("HEADER SECTION:")
        print(header_section.decode("utf-8"))

        print("BODY:")
        print(body.decode("utf-8"))

        client_socket.close()
        print(f"Disconnected from {client_address}")





if __name__ == "__main__":
    print("Starting up server...")
    server = TCPServer()
    server.start_server()



    
