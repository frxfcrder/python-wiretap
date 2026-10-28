import socket
import time

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
SOCKET_TIMEOUT = 3


def create_connection():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(SOCKET_TIMEOUT)
    client.connect((SERVER_HOST, SERVER_PORT))
    return client


def receive_response(client):
    response = bytearray()

    while True:
        try:
            data = client.recv(4096)
        except TimeoutError:
            raise AssertionError("Timed out waiting for server response")

        if not data:
            break

        response.extend(data)

    return bytes(response)


def parse_response(response):
    header_section, separator, body = response.partition(b"\r\n\r\n")

    if not separator:
        raise AssertionError("Response is missing the header/body separator")

    lines = header_section.split(b"\r\n")
    status_line = lines[0].decode("ascii", errors="replace")

    _headers = {}
    for line in lines[1:]:
        if b":" not in line:
            continue

        key, value = line.split(b":", 1)
        _headers[key.decode("ascii").strip().lower()] = value.decode("ascii").strip()

    return status_line, _headers, body


def assert_response(response, expected_status):
    if not response:
        raise AssertionError("Server closed the connection without a response")

    status_line, _headers, body = parse_response(response)

    assert status_line == expected_status, (
        f"Expected {expected_status!r}, got {status_line!r}"
    )

    assert "content-length" in _headers, "Missing Content-Length header"

    expected_length = int(_headers["content-length"])
    actual_length = len(body)

    assert actual_length == expected_length, (
        f"Content-Length mismatch: header says {expected_length}, "
        f"received {actual_length} body bytes"
    )

    return status_line, _headers, body


def send_request_and_receive(request_parts):
    with create_connection() as client:
        for part in request_parts:
            client.sendall(part)

        return receive_response(client)


def make_headers(content_length):
    return (
        f"POST /about HTTP/1.1\r\n"
        f"Host: {SERVER_HOST}:{SERVER_PORT}\r\n"
        f"Content-Length: {content_length}\r\n"
        "Content-Type: text/plain\r\n"
        "\r\n"
    ).encode("ascii")


def test_chunked_body_arrival():
    print("\n--- TEST 1: Body sent in separate pieces ---")

    body_part_1 = b"Hello, from "
    body_part_2 = b"wiretap!"
    expected_body = body_part_1 + body_part_2

    assert len(expected_body) == 20

    response = (
        send_request_and_receive(
            [
                make_headers(len(expected_body)),
                body_part_1,
                b"",
            ]
        )
        if False
        else None
    )

    with create_connection() as client:
        client.sendall(make_headers(len(expected_body)))
        time.sleep(0.2)

        client.sendall(body_part_1)
        time.sleep(0.2)

        client.sendall(body_part_2)
        response = receive_response(client)

    status, _headers, body = assert_response(response, "HTTP/1.1 200 OK")

    print(f"Status: {status}")
    print(f"Response body: {body.decode('utf-8', errors='replace')}")
    print("[PASS] Complete body received and successful response validated.")


def test_disconnect_mid_body():
    print("\n--- TEST 2: Client disconnects mid-body ---")

    client = create_connection()

    try:
        client.sendall(make_headers(20))
        client.sendall(b"Hello")
    finally:
        client.close()

    time.sleep(0.2)

    response = send_request_and_receive(
        [
            (
                f"GET / HTTP/1.1\r\n"
                f"Host: {SERVER_HOST}:{SERVER_PORT}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode("ascii")
        ]
    )

    assert_response(response, "HTTP/1.1 200 OK")
    print("[PASS] Server remained operational after the client disconnected.")
    print("       Inspect server logs to confirm the incomplete request was dropped.")


def test_incomplete_body_returns_400():
    print("\n--- TEST 3: Incomplete body returns 400 ---")

    with create_connection() as client:
        client.sendall(make_headers(50))
        client.sendall(b"Short body")
        client.shutdown(socket.SHUT_WR)

        response = receive_response(client)

    status, _headers, body = assert_response(response, "HTTP/1.1 400 Bad Request")

    expected_body = b"Error: Incomplete request body."

    assert body == expected_body, f"Unexpected error response body: {body!r}"
    assert int(_headers["content-length"]) == len(expected_body)

    print(f"Status: {status}")
    print(f"Content-Length: {_headers['content-length']}")
    print("[PASS] Incomplete request rejected with correctly framed 400 response.")


def test_malformed_content_length():
    print("\n--- TEST 4: Malformed Content-Length ---")

    request = (
        f"POST /about HTTP/1.1\r\n"
        f"Host: {SERVER_HOST}:{SERVER_PORT}\r\n"
        "Content-Length: NOT_A_NUMBER\r\n"
        "Content-Type: text/plain\r\n"
        "\r\n"
        "Hello!"
    ).encode("ascii")

    response = send_request_and_receive([request])

    status, _headers, body = assert_response(response, "HTTP/1.1 400 Bad Request")

    print(f"Status: {status}")
    print(f"Response body: {body.decode('utf-8', errors='replace')}")
    print("[PASS] Malformed Content-Length rejected with 400.")


def run_test(name, test_function):
    try:
        test_function()
    except (AssertionError, OSError, ValueError) as error:
        print(f"[FAIL] {name}: {error}")
        return False

    return True


if __name__ == "__main__":
    print("Starting Wiretap integration tests...")
    print(f"Target: {SERVER_HOST}:{SERVER_PORT}")

    tests = [
        ("Chunked body arrival", test_chunked_body_arrival),
        ("Mid-body disconnect", test_disconnect_mid_body),
        ("Incomplete body response", test_incomplete_body_returns_400),
        ("Malformed Content-Length", test_malformed_content_length),
    ]

    results = [run_test(name, test_function) for name, test_function in tests]

    passed = sum(results)
    failed = len(results) - passed

    print(f"\nResults: {passed} passed, {failed} failed.")

    if failed:
        raise SystemExit(1)
