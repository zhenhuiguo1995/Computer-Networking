import config
import os

command = 'memcached -p {0}'.format(config.CACHE_PORT)
os.system(command)
