import socket
import threading
import time
import struct
import config

BUF_SIZE = 16


def receive_all(length, conn):
    i = 0
    cache = bytes()
    while len(cache) < length:
        cache += conn.recv(min(BUF_SIZE, length - conn))
    return cache


def handler(conn, addr):
    print("Starting to evaluate expressions from a new client")
    byte_expression_number = receive_all(2, conn)
    response = bytes()
    response += byte_expression_number
    expression_number = struct.unpack('!h', byte_expression_number)[0]
    index = 0
    while index < expression_number:
        expression_length = struct.unpack('!h', receive_all(2, conn))[0]
        byte_expression = receive_all(expression_length, conn)
        response += calculator(byte_expression)
        index += 1
        # simulating long running program
        time.sleep(5)
    conn.sendall(response)
    print('finished evaluating all expressions')
    conn.close()


def calculator(byte_expression):
    expression = struct.unpack('!%ds' % len(byte_expression),
                               byte_expression)[0]
    return evaluate(expression.decode('utf-8'))


def evaluate(expression):
    sign = 1
    i = 0
    num = 0
    ans = 0
    while i < len(expression):
        if expression[i] == '+':
            ans += sign * num
            sign = 1
            num = 0
        elif expression[i] == '-':
            ans += sign * num
            sign = -1
            num = 0
        else:
            num = num * 10 + int(expression[i])
        i += 1
    ans += sign * num
    print("The result is: {0} = {1}".format(expression, ans))
    str_ans = str(ans)
    return struct.pack("!h%ds" % len(str_ans),
                       len(str_ans), str_ans.encode('utf-8'))


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((config.EXPRESSION_EVAL_SERVER, config.EXPRESSION_EVAL_PORT))
s.listen()
print('Server started. Waiting for connection...')


while True:
    conn, addr = s.accept()
    print('Server connected by', addr)
    threading.Thread(target=handler, args=(conn, addr)).start()
