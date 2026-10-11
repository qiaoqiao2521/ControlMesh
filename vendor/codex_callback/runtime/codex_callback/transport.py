"""Minimal RFC 6455 text transport for the existing local Unix daemon only.

No TCP, TLS, proxy, compression, or extension negotiation is provided. Partial
frames and fragmented messages survive receive timeouts between task events.
"""

import base64
import hashlib
import secrets
import socket
import struct
import time

MAX_MESSAGE_BYTES = 64 * 1024 * 1024
MAX_HEADER_BYTES = 16 * 1024
ACCEPT_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class ProtocolError(ValueError):
    """The local endpoint did not speak the supported WebSocket protocol."""


class UnixWebSocket:
    """Exchange UTF-8 messages with a WebSocket server over an AF_UNIX socket."""

    def __init__(self, path, timeout=20):
        self.timeout = timeout
        self.buffer = bytearray()
        self.fragment = None
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.settimeout(timeout)
            self.sock.connect(str(path))
            self._handshake()
        except BaseException:
            self.sock.close()
            raise

    def _read_more(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Waiting for a Codex WebSocket message")
        self.sock.settimeout(remaining)
        data = self.sock.recv(65536)
        if not data:
            raise ConnectionError("Codex disconnected")
        self.buffer.extend(data)

    def _need(self, size, deadline):
        while len(self.buffer) < size:
            self._read_more(deadline)

    def _handshake(self):
        """Upgrade to WebSocket and verify the server's accept challenge."""
        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        request = (
            "GET / HTTP/1.1\r\nHost: localhost\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        deadline = time.monotonic() + self.timeout
        while b"\r\n\r\n" not in self.buffer:
            if len(self.buffer) > MAX_HEADER_BYTES:
                raise ProtocolError("WebSocket upgrade headers exceed 16 KiB")
            self._read_more(deadline)
        end = self.buffer.index(b"\r\n\r\n")
        if end > MAX_HEADER_BYTES:
            raise ProtocolError("WebSocket upgrade headers exceed 16 KiB")
        lines = bytes(self.buffer[:end]).decode("iso-8859-1").split("\r\n")
        del self.buffer[: end + 4]
        if lines[0].split()[:2] != ["HTTP/1.1", "101"]:
            raise ProtocolError(f"WebSocket upgrade rejected: {lines[0]}")
        headers = {}
        for line in lines[1:]:
            name, separator, value = line.partition(":")
            if not separator:
                raise ProtocolError("Malformed WebSocket upgrade header")
            name = name.strip().lower()
            value = value.strip()
            headers[name] = headers[name] + ", " + value if name in headers else value

        def tokens(name):
            return {part.strip().lower() for part in headers.get(name, "").split(",")}

        expected = base64.b64encode(
            hashlib.sha1(
                (key + ACCEPT_GUID).encode("ascii"), usedforsecurity=False
            ).digest()
        ).decode("ascii")
        if (
            "websocket" not in tokens("upgrade")
            or "upgrade" not in tokens("connection")
            or headers.get("sec-websocket-accept") != expected
            or "sec-websocket-extensions" in headers
            or "sec-websocket-protocol" in headers
        ):
            raise ProtocolError("Invalid or unsupported WebSocket upgrade response")

    def _send_frame(self, opcode, payload):
        """Mask every client frame, including pong and close frames."""
        size = len(payload)
        if size > MAX_MESSAGE_BYTES:
            raise ProtocolError("WebSocket message exceeds 64 MiB")
        if size < 126:
            header = bytes((0x80 | opcode, 0x80 | size))
        elif size < 65536:
            header = bytes((0x80 | opcode, 0xFE)) + struct.pack("!H", size)
        else:
            header = bytes((0x80 | opcode, 0xFF)) + struct.pack("!Q", size)
        mask = secrets.token_bytes(4)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        self.sock.settimeout(self.timeout)
        self.sock.sendall(header + mask + masked)

    def send(self, text):
        self._send_frame(1, text.encode("utf-8"))

    def _frame(self, deadline):
        """Consume a frame only after all bytes arrive, preserving partial reads."""
        self._need(2, deadline)
        first, second = self.buffer[:2]
        final, opcode = bool(first & 0x80), first & 0x0F
        if first & 0x70 or second & 0x80 or opcode not in {0, 1, 8, 9, 10}:
            raise ProtocolError("Unsupported WebSocket frame flags or opcode")
        size = second & 0x7F
        if opcode >= 8 and (not final or size > 125):
            raise ProtocolError("Invalid WebSocket control frame")
        offset = 2
        if size in {126, 127}:
            count = 2 if size == 126 else 8
            offset += count
            self._need(offset, deadline)
            decoded = int.from_bytes(self.buffer[2:offset], "big")
            if decoded < (126 if count == 2 else 65536) or decoded >= 2**63:
                raise ProtocolError("Invalid WebSocket length encoding")
            size = decoded
        message_size = size + (len(self.fragment or b"") if opcode < 8 else 0)
        if message_size > MAX_MESSAGE_BYTES:
            raise ProtocolError("WebSocket message exceeds 64 MiB")
        self._need(offset + size, deadline)
        payload = bytes(self.buffer[offset : offset + size])
        del self.buffer[: offset + size]
        return final, opcode, payload

    def recv(self, timeout):
        """Return one text message, handling control frames between fragments."""
        deadline = time.monotonic() + timeout
        while True:
            final, opcode, payload = self._frame(deadline)
            if opcode == 8:
                if len(payload) == 1:
                    raise ProtocolError("Invalid WebSocket close payload")
                self.close(payload)
                raise ConnectionError("Codex closed the WebSocket")
            if opcode == 9:
                self._send_frame(10, payload)
                continue
            if opcode == 10:
                continue
            if opcode == 1:
                if self.fragment is not None:
                    raise ProtocolError("New message before previous fragments ended")
                self.fragment = bytearray()
            elif self.fragment is None:
                raise ProtocolError("Unexpected WebSocket continuation")
            self.fragment.extend(payload)
            if final:
                text = self.fragment.decode("utf-8")
                self.fragment = None
                return text

    def close(self, payload=b"\x03\xe8"):
        """Attempt the closing handshake without masking the caller's exception."""
        if self.sock.fileno() < 0:
            return
        try:
            self._send_frame(8, payload)
        except OSError:
            pass
        finally:
            self.sock.close()
