from __future__ import with_statement
import hashlib
import datetime
import pickle
import copy
import threading
import decorator

expires = datetime.timedelta(days=1)
cache = {}
_cache_lock = threading.Lock()

@decorator.decorator
def memoize(f, *args, **kwargs):
    key = f.__name__ + str(args[1:]) + str(kwargs)
    key = hashlib.md5(key).hexdigest()
    now = datetime.datetime.now()

    with _cache_lock:
        if key in cache and cache[key]['timestamp'] + expires > now:
            return cache[key]['result']

    with _cache_lock:
        if key in cache and cache[key]['timestamp'] + expires < now:
            del cache[key]

    result = f(*args, **kwargs)

    with _cache_lock:
        cache[key] = {
            'timestamp' : now,
            'result' : result,
        }

    return result
