import http.server
from http.server import BaseHTTPRequestHandler
import config
import time


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
            # the request is not valid
            self.send_response(404)
        # TODO: implement logic to handle GET request of different URL path

    def do_POST(self):
        if self.path == config.EVAL_EXPRESSION:
            # connect to expression_eval_server to get a response
            # TODO: set a connection with expression_eval_server and get a response
            response = 12
            self.send_response(200, response)
        else:
            # TODO: this is a invalid request
            self.send_response(404)


s = http.server.ThreadingHTTPServer(('localhost', 8181), Handler)
s.serve_forever()
