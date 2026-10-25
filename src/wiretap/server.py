import socket
import threading
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

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
        logger.info("Server listening on http://%s:%s", self.host, self.port)

        
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                logger.info("Connection from %s", client_address)

                client_thread = threading.Thread(
                    target = self._handle_client,
                    args = (client_socket, client_address),
                )
                client_thread.start()

            except OSError as exc:
                logger.exception("Accept failed")
                break

       
    def _handle_client(self, client_socket, client_address):
        buffer = b""

        while b"\r\n\r\n" not in buffer:
            data = client_socket.recv(1024)
            if not data:
                return
            buffer += data

        logger.debug("Received request:\n%s", buffer.decode("utf-8"))
        
        header_section, separator, body = buffer.partition(b"\r\n\r\n")

        header_lines = header_section.split(b"\r\n")
        
        logger.debug("Raw buffer: %r", buffer)
        logger.debug("Body bytes: %r", body)
        logger.debug("Body length: %d bytes", len(body))
        
        request_line= header_lines[0].decode("utf-8")
        method, target, version = request_line.split()

        headers = {}
        for line in header_lines[1:]:
            line = line.decode("utf-8")

            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()


        content_length = int(headers.get("content-length", 0))

        try:
            while len(body) < content_length:
                remaining = content_length - len(body)
                data = client_socket.recv(min(1024, remaining))

                if not data:
                    logging.info("Client disconnected while sending body data")
                    break
                
                body += data
                    
        except OSError:
            logger.debug("Network error while reading request body")

        finally:
            remaining = max(0, content_length - len(body))
            client_socket.close()
            logger.debug(f"Body bytes received: {len(body)}")
            logger.info(f"Body bytes remaining: {remaining}")


        
        logger.debug("Parsed headers: %s", headers)
        logger.debug("Request: %s %s %s", method, target, version)
        logger.debug("Header section:\n%s", header_section.decode("utf-8"))
        logger.debug("Body:\n%s", body.decode("utf-8"))

        logger.info("Disconnected from %s", client_address)




if __name__ == "__main__":
    print("Starting up server...")
    server = TCPServer()
    server.start_server()



    
