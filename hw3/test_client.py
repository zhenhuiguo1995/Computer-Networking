import http.client
from config import *

conn = http.client.HTTPConnection(WEB_API_SERVER, WEB_API_PORT)

# test /api/gettime
"""
conn.request('GET', '/api/gettime')
r = conn.getresponse()
print(r.status, r.reason)
time.sleep(3)
"""

# test /html.status
"""
conn.request('GET', '/html.status')
r = conn.getresponse()
print(r)
"""

body = '1+2+3+6'
conn.request('POST', '/api/evalexpression', body)
r = conn.getresponse()
print(r.status, r.reason)
cache = r.read(2)
print(cache)
