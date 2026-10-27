import socket


def client():
    status_code = {
        200: "200 OK",
        201: "201 Created",
        204: "204 No Content",
        301: "301 Moved Permanently",
        302: "302 Found",
        400: "400 Bad Request",
        401: "401 Unauthorized",
        403: "403 Forbidden",
        404: "404 Not Found",
        405: "405 Method Not Allowed",
        500: "500 Internal Server Error",
        503: "503 Service Unavailable",
    }

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ("127.0.0.1", 8000)
    client_socket.connect(server_address)

    body = "Hello, from wiretap!"
    content_length = len(body.encode("utf-8"))

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
        client_socket.sendall(raw_request.encode("utf-8"))
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
        decoded = response.decode("utf-8", errors="replace")
        try:
            status_line = decoded.split("\r\n", 1)[0]
            code = int(status_line.split(" ", 2)[1])
            print(f"Status: {status_code.get(code, code)}")
        except (IndexError, ValueError):
            print("Status: Could not parse response status line")
        print(decoded)
    else:
        print("[No data received to display]")


if __name__ == "__main__":
    client()
