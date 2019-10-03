import socket
import api
import utils
from config import *


host_name = socket.getfqdn()
print("Hostname is", host_name)
host_ip = socket.gethostbyname(host_name)
print("Host IP address is ", host_ip)
host_port = 80
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host_ip, host_port))
s.listen()
print("Server started. Waiting for connecting...")


def handler(conn):
    api_name, http_version = utils.read_request_line(conn)
    if api_name == EVAL_EXPRESSION:
        api.evaluate(conn, http_version)
    elif api_name == GET_TIME:
        api.get_time(conn, http_version)
    elif api_name == BAD_REQUEST:
        api.bad_request(conn, http_version)
    else:
        # api_name == REQUEST_NOT_FOUND
        api.request_not_found(conn, http_version)


while True:
    # wait for next client
    conn, addr = s.accept()
    print("Server connected by ", addr, " at ", utils.now())
    handler(conn)

    # close tcp connection
    conn.close()
    print("Server finished talking with ", addr, " at ", utils.now())