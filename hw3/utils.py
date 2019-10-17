import struct
import config
import time

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


def generate_response_from_cache_server(cache_client):
    eval_list = generate_data(cache_client.get(config.EVAL_EXPRESSION)
                              .decode('utf-8').split(config.SEPARATOR))
    gettime_list = generate_data(cache_client.get(config.GET_TIME)
                                 .decode('utf-8').split(config.SEPARATOR))
    response = '''
    <html>
    <h1> API count information</h1>
    <h3>/api/evalexpression</h3>
    <ul>
        <li>last minute: {0}</li>
        <li>last hour: {1}</li>
        <li>last 24 hours: {2}</li>
        <li>lifetime: {3}</li>
    </ul>
    <h3>/api/gettime</h3>
    <ul>
        <li>last minute: {4}</li>
        <li>last hour: {5}</li>
        <li>last 24 hours: {6}</li>
        <li>lifetime: {7}</li>
    </ul>
    </html>
    '''.format(eval_list[0], eval_list[1], eval_list[2], eval_list[3],
               gettime_list[0], gettime_list[1], gettime_list[2], gettime_list[3])
    return response.encode('utf-8')


def generate_data(records):
    now = time.time()
    last_minute = 0
    last_hour = 0
    last_day = 0
    for record in records:
        diff = float(now) - float(record)
        if diff <= 60:
            last_minute += 1
        if diff <= 60 * 60:
            last_hour += 1
        if diff <= 60 * 60 * 24:
            last_day += 1
    life_time = len(records)
    return [last_minute, last_hour, last_day, life_time]


def generate_response_for_get_time():
    return time.ctime().encode('utf-8')