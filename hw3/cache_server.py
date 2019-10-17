import pymemcache
import config


cache = pymemcache.client.base.Client(
    (config.CACHE_SERVER, config.CACHE_PORT))