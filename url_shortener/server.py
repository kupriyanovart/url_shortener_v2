import socket
from datetime import datetime
from email.parser import Parser

MAX_LINE = 64 * 1024
MAX_HEADERS = 100


class Server:
    request_queue_size = 1

    def __init__(self, server_address, request_handler):
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.listen_socket.bind(server_address)
        self.listen_socket.listen(self.request_queue_size)

        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

        self.conn = None
        self.request_data = None

        self.request_handler = request_handler

        self._response_status = None
        self._response_headers = {}

    def serve_forever(self):
        while True:
            self.conn, client_address = self.listen_socket.accept()
            with self.conn:
                self.handle_one_request()

    def handle_one_request(self):
        self.request_data = self.conn.recv(4096).decode("utf-8")
        environ = self.get_environ()
        result = self.request_handler(environ, self.start_response)

        self.finish_response(result)

    def start_response(self, status, response_headers):
        # Add necessary server headers
        server_headers = [{
            "date": datetime.now().__str__(),
        }]
        all_headers = {}

        all_headers.update(**response_headers)
        all_headers.update(*server_headers)
        self._response_status = status
        self._response_headers = all_headers
        # return self.finish_response

    def finish_response(self, result):
        if self._response_status:
            response = f"HTTP/1.1 {self._response_status}\r\n"
            for key, value in self._response_headers.items():
                response += f"{key}: {value}\r\n"

            if result:
                response += "\r\n"
                response += result

            response_bytes = response.encode()
            self.conn.sendall(response_bytes)

    def get_environ(self):
        env = {}

        method, path, ver, headers = self.parse_request()

        env["wsgi.version"] = (1, 0)
        env["wsgi.url_scheme"] = "http"
        env["wsgi.multithread"] = False
        env["wsgi.multiprocess"] = False
        env["wsgi.run_once"] = False

        env["REQUEST_METHOD"] = method
        env["SCRIPT_NAME"] = ""
        env["SERVER_NAME"] = self.server_name
        env["SERVER_PROTOCOL"] = ver
        env["SERVER_PORT"] = self.server_port
        if path.find("?") >= 0:
            env["PATH_INFO"] = path.split("?")[0]
            env["QUERY_STRING"] = path.split("?")[1]
        else:
            env["PATH_INFO"] = path

        if "content-type" in headers:
            env["CONTENT_TYPE"] = headers.get("content-type")
        env["wsgi.input"] = self.request_data
        for name, value in headers.items():
            key = "HTTP_" + name.replace("-", "_").upper()
            if key in env:
                value = "{0},{1}".format(env[key], value)
            env[key] = value
        return env

    def parse_request(self):

        method, target, ver = self.parse_request_line()
        headers = self.parse_headers()
        host = headers.get("Host")
        if not host:
            raise HTTPError(400, "Bad request", "Host header is missing")
        return method, target, ver, headers

    def parse_request_line(self):
        raw = self.request_data.splitlines()[0]
        if len(raw) > MAX_LINE:
            raise HTTPError(400, "Bad request",
                            "Request line is too long")

        words = raw.split()
        if len(words) != 3:
            raise HTTPError(400, "Bad request",
                            "Malformed request line")

        method, target, ver = words
        if ver != "HTTP/1.1":
            raise HTTPError(505, "HTTP Version Not Supported")
        return method, target, ver

    def parse_headers(self):
        headers_list = []
        for i, line in enumerate(self.request_data.splitlines()):
            if i == 0:
                continue
            if line in (b"\r\n", b"\n", b""):
                break

            headers_list.append(line)
            if len(headers_list) > MAX_HEADERS:
                raise HTTPError(494, "Too many headers")

        headers = "\n".join(headers_list)
        return Parser().parsestr(headers)


class HTTPError(Exception):
    def __init__(self, status, reason, body=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body
