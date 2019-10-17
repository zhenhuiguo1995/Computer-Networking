import http
import socket
from http.server import BaseHTTPRequestHandler

import pymemcache

from config import *
import time
from utils import *


def get_response_from_eval_server(data):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((EXPRESSION_EVAL_SERVER, EXPRESSION_EVAL_PORT))
    conn.sendall(encode_expression(data))
    length = struct.unpack("!h", receive_all(conn, 2))[0]
    response = decode_expressions(conn, length)
    conn.close()
    return response


def get_response_from_cache_server():
    return 1


def save(key, value):
    byte_string = cache_client.get(key)
    if byte_string is None:
        cache_client.add(key, value)
    else:
        byte_string += (SEPARATOR + value)
        cache_client.set(key, byte_string)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == GET_TIME:
            save(GET_TIME, time.time())
            response = time.ctime()
            self.send_response(200, response)
        elif self.path == STATUS:
            # connect to cache server and get a html as a response
            response = get_response_from_cache_server()
            self.send_response(200, response)
        else:
            self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length'))
        data = self.rfile.read(length)
        save(EVAL_EXPRESSION, data)
        if self.path == EVAL_EXPRESSION:
            response = get_response_from_eval_server(data)
            self.send_response(200, response)
        else:
            self.send_response(404)
        self.end_headers()


cache_client = pymemcache.client.base.Client((CACHE_SERVER, CACHE_PORT))
s = http.server.ThreadingHTTPServer((WEB_API_SERVER, WEB_API_PORT), Handler)
s.serve_forever()
