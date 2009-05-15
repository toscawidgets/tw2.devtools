import tw.core as twc

def request_local_tst():
#    if _request_id is None:
#        raise KeyError('must be in a request')
    try:
        return _request_local[_request_id]
    except KeyError:
        rl_data = {}
        _request_local[_request_id] = rl_data
        return rl_data

twc.core.request_local = request_local_tst

def setup():
    global _request_local, _request_id
    _request_local = {}
    _request_id = None

def request(requestid):
    global _request_id
    _request_id = requestid
    return request_local_tst()
