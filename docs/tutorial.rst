Tutorial
--------

This tutorial will show you how to get ToscaWidgets 2 working with a WSGI application. We'll start by creating a simple WSGI app; create ``myapp.py`` containing the following::

    import webob as wo, wsgiref as wr

    def simple_app(environ, start_response):
        req = wo.Request(environ)
        resp = wo.Response(request=req, content_type="text/html; charset=UTF8")
        resp.body = 'hello world'
        return resp(environ, start_response)

    if __name__ == "__main__":
        wr.simple_server.make_server('', 8000, app).serve_forever()

To check this works, run ``myapp.py``, and use a web browser to open ``http://localhost:8000/``. You should see ``hello world``.

install tw middleware
do a sample widget
validation
