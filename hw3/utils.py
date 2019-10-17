import struct

BUF_SIZE = 16


def receive_all(conn, length):
    cache = bytes()
    while len(cache) < length:
        cache += conn.recv(min(BUF_SIZE, length - len(cache)))
    return cache


def encode_expression(expression):
    return struct.pack("!h", len(expression)) + expression


def decode_expressions(conn, length):
    cache = receive_all(conn, length)
    expression_result = struct.unpack("!%ds" % len(cache), cache)[0]
    return str(expression_result)
