import time
from tw2.devtools import memoize

def basic_test():
    @memoize.memoize
    def f():
        time.sleep(2)
        return 5

    start1 = time.time()
    assert(f() == 5)
    end1  = time.time()
    start2 = time.time()
    assert(f() == 5)
    end2  = time.time()
    assert(end1-start1 > end2-start2)

