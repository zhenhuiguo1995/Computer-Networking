import http
import socket
from http.server import BaseHTTPRequestHandler
import pymemcache
from config import *
from utils import *
from utils import generate_response_for_get_time


def get_response_from_eval_server(data):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((EXPRESSION_EVAL_SERVER, EXPRESSION_EVAL_PORT))
    conn.sendall(encode_expression(data))
    length = struct.unpack("!h", receive_all(conn, 2))[0]
    response = decode_expressions(conn, length)
    conn.close()
    return response


def save(key):
    byte_string = cache_client.get(key)
    if byte_string is None:
        cache_client.add(key, time.time())
    else:
        byte_string += (SEPARATOR + str(time.time())).encode('utf-8')
        cache_client.set(key, byte_string)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == GET_TIME:
            save(GET_TIME)
            response = generate_response_for_get_time()
            self.send_response(200)
            self.send_header(CONTENT_LENGTH_HEADER, len(response))
            self.end_headers()
            self.wfile.write(response)
        elif self.path == STATUS:
            response = generate_response_from_cache_server(cache_client)
            self.send_response(200)
            self.send_header(CONTENT_LENGTH_HEADER, len(response))
            self.end_headers()
            self.wfile.write(response)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length'))
        data = self.rfile.read(length)
        save(EVAL_EXPRESSION)
        if self.path == EVAL_EXPRESSION:
            response = get_response_from_eval_server(data)
            self.send_response(200)
            self.send_header(CONTENT_LENGTH_HEADER, len(response))
            self.end_headers()
            self.wfile.write(response)
        else:
            self.send_response(404)
            self.end_headers()


cache_client = pymemcache.client.base.Client((CACHE_SERVER, CACHE_PORT))
s = http.server.ThreadingHTTPServer((WEB_API_SERVER, WEB_API_PORT), Handler)
s.serve_forever()
