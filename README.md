# python-wiretap

A Python-based HTTP traffic inspector built to explore
networking, TCP sockets, and HTTP request/response handling.

## Goals

- [x] Build a basic TCP server and client
- [x] Understand HTTP message structure
- [x] Implement a local HTTP proxy
- [x] Inspect request and response metadata
- [x] Add traffic logging and automated tests

## What's inside

| File | Purpose |
|------|---------|
| `src/wiretap/server.py` | Threaded TCP server that parses HTTP requests (request line, headers, body) and replies |
| `src/wiretap/client.py` | Minimal client that sends a `POST` request and prints the response |
| `src/wiretap/proxy.py`  | Local HTTP proxy: forwards requests to an upstream, rewrites absolute-form URLs to origin-form, and relays responses back |
| `src/wiretap/logging_setup.py` | Logging configuration — console log plus JSON-lines `traffic.log` |
| `src/wiretap/templates/status_codes.html` | Template for the status code page served at `/status` |
| `tests/test_script.py` | Integration tests for the server (run it while the server is up) |

## Run it

```bash
# 1. Start the server (listens on 127.0.0.1:8000)
python src/wiretap/server.py

# 2. Optionally start the proxy (listens on 127.0.0.1:8888, upstream 127.0.0.1:8000)
python src/wiretap/proxy.py

# 3. Run the integration tests against the server
python tests/test_script.py
```

Then open in a browser:

- `http://127.0.0.1:8000/status` (or `/`) — lists every status code the server supports
- Send requests through the proxy on port `8888` to watch them get forwarded
  (e.g. `GET http://127.0.0.1:8000/about HTTP/1.1`)

Every request, response, and proxied exchange is written to `traffic.log`
as one JSON object per line:

```json
{"time": "2026-10-28T13:18:24.823", "event": "response", "client": "127.0.0.1:62035", "status": 200, "reason": "OK", "bytes": 1200}
```

## Status

Core goals implemented: server, client, HTTP message handling, local proxy,
metadata inspection, JSON traffic logging, and an integration test suite.
HTTPS tunneling (`CONNECT`) and a request-viewer dashboard are possible next steps.
