import utils
import re
from config import *


def evaluate(conn, http_version):
    content_length_line = utils.read_line(conn)
    content_length = int(re.match(CONTENT_LENGTH_PATTERN, content_length_line)[1])
    expression = utils.read_body_line(content_length, conn)
    result = utils.calculator(expression)
    return utils.response(result, EVAL_EXPRESSION, http_version)


def get_time(conn, http_version):
    pass


def request_not_found(conn, http_version):
    # send a http 404 response(not found) for
    # unsupported url
    pass


def bad_request(conn, http_version):
    # send a http 400 response (bad request) for
    # unsupported arithmetic expressions
    pass