import http.client
from config import *
import time

conn = http.client.HTTPConnection(WEB_API_SERVER, WEB_API_PORT)

# test /api/gettime
conn.request('GET', '/api/gettime')
r = conn.getresponse()
print(r)
time.sleep(3)

# test /html.status
conn.request('GET', '/html.status')
r = conn.getresponse()
print(r)