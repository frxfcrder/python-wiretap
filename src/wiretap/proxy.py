import socket
import threading
from urllib.parse import urlsplit

from logging_setup import log_traffic, logger, write_intercept


class HTTPProxy:
    def __init__(self, host="127.0.0.1", port=8888):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start_proxy(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        logger.info(f"Proxy intercepting on {self.host}:{self.port}")

        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
            except OSError:
                logger.exception("Proxy accept failed")
                break

            logger.info("Connection from %s", client_address)

            client_thread = threading.Thread(
                target=self._handle_proxy,
                args=(client_socket, client_address),
                daemon=True,
            )
            client_thread.start()

    def _handle_proxy(self, client_socket, client_address):
        address_str = f"{client_address[0]}:{client_address[1]}"

        buffer = b""
        client_socket.settimeout(15.0)

        while b"\r\n\r\n" not in buffer:
            data = client_socket.recv(1024)
            if not data:
                log_traffic(
                    {
                        "event": "proxy-request",
                        "client": address_str,
                        "method": None,
                        "target": None,
                        "note": "connection closed before completing request",
                    }
                )
                return
            buffer += data

        header_section, _separator, body = buffer.partition(b"\r\n\r\n")
        header_lines = header_section.split(b"\r\n")

        try:
            request_line = header_lines[0].decode("utf-8")
            method, target, version = request_line.split()
        except (ValueError, IndexError):
            client_socket.close()
            return

        _headers = {}
        for line in header_lines[1:]:
            line = line.decode("utf-8")

            if ":" in line:
                key, value = line.split(":", 1)
                _headers[key.strip().lower()] = value.strip()

        body_text = body.decode("utf-8", errors="ignore")

        write_intercept(
            ip=address_str,
            method=method,
            url=target,
            payload_size=len(body),
            payload=body_text,
        )

        target_host = None
        target_port = 80
        forward_path = target
        parsed_url = None

        if target.startswith(("http://", "https://")):
            try:
                parsed_url = urlsplit(target)
            except ValueError:
                logger.exception("urlsplit encountered a malformed URI layout")
                client_socket.close()
                return

            if not parsed_url.netloc:
                logger.info("Absolute URL is missing a host: %r", target)
                client_socket.close()
                return

            if parsed_url.scheme == "https":
                logger.info("HTTPS targets need CONNECT tunneling - not supported yet")
                client_socket.close()
                return

            target_host = parsed_url.hostname
            try:
                target_port = parsed_url.port or 80
            except ValueError:
                logger.info("Invalid port in URL: %r", target)
                client_socket.close()
                return

            forward_path = parsed_url.path or "/"
            if parsed_url.query:
                forward_path += "?" + parsed_url.query

        else:
            host_header = _headers.get("host", "")
            if host_header:
                target_host = host_header
                if ":" in host_header:
                    target_host, port_str = host_header.split(":", 1)
                    try:
                        target_port = int(port_str)
                    except ValueError:
                        target_port = 80

        if not target_host:
            logger.info("No upstream host could be resolved for %r", target)
            client_socket.close()
            return

        rewritten_header_lines = [f"{method} {forward_path} {version}"]
        for line in header_lines[1:]:
            line = line.decode("utf-8")

            if ":" in line:
                key = line.split(":", 1)[0].strip().lower()
            else:
                key = ""

            if key == "host":
                rewritten_header_lines.append(f"Host: {target_host}:{target_port}")
            else:
                rewritten_header_lines.append(line)

        forward_buffer = ("\r\n".join(rewritten_header_lines) + "\r\n\r\n").encode(
            "utf-8"
        ) + body

        log_traffic(
            {
                "event": "proxy-request",
                "client": address_str,
                "method": method,
                "target": target,
                "upstream": f"{target_host}:{target_port}",
            }
        )

        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.settimeout(15.0)

        try:
            remote_socket.connect((target_host, target_port))
            remote_socket.sendall(forward_buffer)

            while True:
                remote_data = remote_socket.recv(4096)
                if not remote_data:
                    break

                client_socket.sendall(remote_data)

            remote_socket.close()

        except OSError as thread_err:
            print(f"[!] Error processing request from {client_address}: {thread_err}")

        finally:
            client_socket.close()


if __name__ == "__main__":
    proxy = HTTPProxy()
    proxy.start_proxy()
