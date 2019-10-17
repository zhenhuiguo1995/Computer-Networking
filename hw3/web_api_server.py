import http.server
from http.server import BaseHTTPRequestHandler
import pymemcache


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        pass
        # TODO: implement logic to handle GET request of different URL path

    def do_POST(self):
        pass
        # TODO: implement logic to handle POST request of different URL path


s = http.server.ThreadingHTTPServer(('localhost', 8181), Handler)
s.serve_forever()

cache = pymemcache.client.base.Client(('localhost', 8182))