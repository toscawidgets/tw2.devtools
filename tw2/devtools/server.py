import tw2.core as twc

def dev_server(
    app=None, host='127.0.0.1', port=8000, logging=True, weberror=True,
    use_threadpool=None, threadpool_workers=10, request_queue_size=5,
    repoze_tm=False, **config):
    """
    Run a development server, hosting the ToscaWidgets application.
    This requires gearbox and WebError, which are only sure to be available if
    tw2.devtools is installed.
    """
    config.setdefault('debug', True)
    config.setdefault('controller_prefix', '/')
    app = twc.make_middleware(app, **config)

    if repoze_tm:
        import repoze.tm as rtm
        import tw2.sqla as tws
        app = rtm.TM(app, tws.commit_veto)

    if weberror:
        import weberror.errormiddleware as we
        app = we.ErrorMiddleware(app, debug=True)

    # TODO - this got left behind in the python3 port.  Revive it.
    #if logging:
    #    import paste.translogger as pt
    #    app = pt.TransLogger(app)

    # Handle old and new versions of gearbox.
    try:
        from gearbox.commands.serve import wsgiref_server_runner
    except ImportError:
        from gearbox.commands.server import wsgiref_server_runner

    wsgiref_server_runner(
        app,
        host=host, port=port,
        use_threadpool=use_threadpool,
        threadpool_workers=threadpool_workers,
        request_queue_size=request_queue_size,
    )

# TBD: autoreload
