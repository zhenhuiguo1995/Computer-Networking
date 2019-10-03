import time
from config import *
import re


def now():
    return time.ctime(time.time())


# reads the line and returns a string representing the information
def read_line(conn):
    line = bytes()
    while len(line) <= 2 or (len(line) > 2 and line[len(line) - 2: len(line)] != END_OF_LINE):
        line += conn.recv(1)
    return line.decode('utf -8')


def read_request_line(conn):
    # read a request line
    line = read_line(conn)
    match_object = re.match(REQUEST_LINE_PATTERN, line)
    url = match_object[1]
    http_version = match_object[2]
    # not all urls are valid
    api_match_object = re.match(API_PATTERN, url)
    if api_match_object is None:
        return REQUEST_NOT_FOUND, http_version
    api = api_match_object[1]
    return api, http_version


def read_body_line(conn, length):
    # read the body line, if there's any
    pass


def save():
    pass


def response(result, api_name, version):
    pass


def calculator(expression):
    pass