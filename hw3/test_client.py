import http.client
from config import *
import time

conn = http.client.HTTPConnection(WEB_API_SERVER, WEB_API_PORT)

"""# test /api/gettime
conn.request('GET', GET_TIME)
r = conn.getresponse()
print(r.status, r.reason)
cache = r.read(int(r.headers.get(CONTENT_LENGTH_HEADER)))
print(cache)
time.sleep(3)"""


body = '1+2+3+6'
conn.request('POST', EVAL_EXPRESSION, body)
r = conn.getresponse()
print(r.status, r.reason)
cache = r.read(int(r.headers.get(CONTENT_LENGTH_HEADER)))
print(cache)
time.sleep(3)

"""# test /html.status
conn.request('GET', STATUS)
r = conn.getresponse()
print(r.status, r.reason)
cache = r.read(int(r.headers.get('Content-Length')))
print(cache)
"""