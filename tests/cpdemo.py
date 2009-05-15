from pkg_resources import require
require('CherryPy>=3.0.0', 'tw.forms', 'Genshi')

import cherrypy as cp, tw.core as twc


class Controller(object):
    @cp.expose
    def index(self, **form_data):
        return 'hello world'


#XXX I'm not sure how can I pass args. to the middleware with CP's config
#    pipeline API, hence this hacky wrapper. Any better way of doing this?
def tw_middleware(app):
    conf = {'toscawidgets.framework.default_view':'genshi'}
    return twc.make_middleware(app, conf, stack_registry=True)


cp_config = {
    '/': {'wsgi.pipeline': [('tw', tw_middleware)]}
}

if __name__ == "__main__":
    cp.quickstart(Controller(), '', cp_config)
