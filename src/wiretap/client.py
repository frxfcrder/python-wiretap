import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('127.0.0.1', 8000)
client_socket.connect(server_address)

body = "Hello, from wiretap!"
content_length = len(body.encode('utf-8'))


raw_request = (
    "POST /about HTTP/1.1\r\n"
    f"Host: {server_address[0]}:{server_address[1]}\r\n"
    f"Content-Length: {content_length}\r\n"
    "Content-Type: text/plain\r\n"
    "\r\n" 
    f"{body}"      
)

response = None
try:
    client_socket.sendall(raw_request.encode('utf-8'))
    response = client_socket.recv(1024)
    if response:
        print("Received from server sucessfully:", response.decode())
    else:
        print("Server closed without response")
except OSError as e:
    print(f"Network Error Occured: {e}")
finally:
    client_socket.close()


print("--- RAW SERVER RESPONSE ---")
if response:
    print(response.decode('utf-8'))
else:
    print("[No data received to display]")