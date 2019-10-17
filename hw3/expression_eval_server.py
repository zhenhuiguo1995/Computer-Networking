import socket
import threading
import config
from utils import *


def handler(conn, addr):
    print("Starting to evaluate expressions from a new client")
    length = struct.unpack('!h', receive_all(conn, 2))[0]
    byte_expression = receive_all(conn, length)
    response = calculator(byte_expression)
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
