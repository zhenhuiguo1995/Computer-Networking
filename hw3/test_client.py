import http.client
from config import *
import time

conn = http.client.HTTPConnection(WEB_API_SERVER, WEB_API_PORT)

# test /api/gettime
conn.request('GET', GET_TIME)
r = conn.getresponse()
cache = r.read(int(r.headers.get(CONTENT_LENGTH_HEADER)))
print("/api/gettime returns: {0}".format(cache.decode('utf-8')))
time.sleep(3)

# test /api/evalexpression
expressions = ['1+2+3+6', '23-145+1+1920', '77+218398139-221']
for i in range(len(expressions)):
    conn.request('POST', EVAL_EXPRESSION, expressions[i])
    r = conn.getresponse()
    cache = r.read(int(r.headers.get(CONTENT_LENGTH_HEADER)))
    print(expressions[i], " = ", cache.decode('utf-8'))
    time.sleep(3)

# test /html.status
conn.request('GET', STATUS)
r = conn.getresponse()
print('/status.html returns the following html:')
cache = r.read(int(r.headers.get('Content-Length')))
print(cache.decode('utf-8'))
