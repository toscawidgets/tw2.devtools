import cherrypy as cp, tw2.core as twc


class Controller(object):
    @cp.expose
    def index(self, **form_data):
        return 'hello world'


#XXX I'm not sure how can I pass args. to the middleware with CP's config
#    pipeline API, hence this hacky wrapper. Any better way of doing this?
def tw_middleware(app):
    conf = {'default_view':'genshi'}
    return twc.make_middleware(app, **conf)


cp_config = {
    '/': {'wsgi.pipeline': [('tw2', tw_middleware)]}
}

if __name__ == "__main__":
    cp.quickstart(Controller(), '', cp_config)
