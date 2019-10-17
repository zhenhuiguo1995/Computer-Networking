import http
import socket
from http.server import BaseHTTPRequestHandler
import config
import time
from utils import *


def get_response_from_eval(data):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((config.EXPRESSION_EVAL_SERVER, config.EXPRESSION_EVAL_PORT))
    conn.sendall(encode_expression(data))
    length = struct.unpack("!h", receive_all(conn, 2))[0]
    response = decode_expressions(conn, length)
    conn.close()
    return response


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == config.GET_TIME:
            response = time.ctime()
            self.send_response(200, response)
        elif self.path == config.STATUS:
            # connect to cache server and get a html as a response
            response = ""
            self.send_response(200, response)
        else:
            self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length'))
        data = self.rfile.read(length)
        if self.path == config.EVAL_EXPRESSION:
            response = get_response_from_eval(data)
            self.send_response(200, response)
        else:
            self.send_response(404)
        self.end_headers()


s = http.server.ThreadingHTTPServer((config.WEB_API_SERVER, config.WEB_API_PORT), Handler)
s.serve_forever()
