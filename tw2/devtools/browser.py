import tw2.core as twc, pkg_resources as pr, docutils.core, os, genshi.input as gsi, re
import tw2.devtools
import tw2.jquery
import tw2.jqplugins.ui
import tw2.protovis.custom
from paste.script import command as pc

import repositories

import inspect
import pygments
import xmlrpclib

import warnings
import memoize

def prepare_source(s):
    try:
        source = inspect.getsource(s)
    except IOError, e:
        warnings.warn(repr(s) + " : " + str(e))
        return ""

    html_args = {'full': False}
    code = pygments.highlight(
        source,
        pygments.lexers.PythonLexer(),
        pygments.formatters.HtmlFormatter(**html_args)
    )

    return code

def rst2html(x, s):
    html = docutils.core.publish_string(s or '', writer_name='html',
        settings_overrides={'template': os.path.dirname(__file__)+'/rststub.txt'})
    html = html.replace('<blockquote>', '')
    html = html.replace('</blockquote>', '')
    return gsi.HTML(html)

class WbPage(twc.Page):
    _no_autoid = True
    resources = [twc.CSSLink(modname=__name__, filename='static/tosca.css'),
                 twc.CSSLink(modname=__name__, filename='static/pygments.css'),
                 twc.DirLink(modname=__name__, filename='static/')]
    enable_repo_metadata = twc.Param()
    enable_pypi_metadata = twc.Param()

    template = "genshi:tw2.devtools.templates.wb_page"
    def prepare(self):
        super(WbPage, self).prepare()
        self.modules = sorted(ep.module_name
                        for ep in pr.iter_entry_points('tw2.widgets')
                        if not ep.module_name.endswith('.samples'))
        self.pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')


    @memoize.memoize
    def commits_per_month(self, module):
        return repositories.commits_per_month(module)

    def has_commits(self, module):
        return self.commits_per_month(module)

    def commits(self, module):
        """ Returns a tw2.protovis spark chart widget """
        class CommitChart(tw2.protovis.custom.SparkBar):
            p_height = 8
            p_data = self.commits_per_month(module)
        return CommitChart

    @memoize.memoize
    def _pypi_versions(self, module):
        versions = self.pypi.package_releases(module, True)
        return versions

    @memoize.memoize
    def pypi_version(self, module):
        versions = self.pypi.package_releases(module)
        if len(versions):
            return versions[0]
        return '----'

    @memoize.memoize
    def pypi_downloads(self, module):
        return sum([
            sum([
                d['downloads'] for d in self.pypi.release_urls(module, version)
            ])
            for version in self._pypi_versions(module)
        ])

class Index(WbPage):
    class child(twc.Widget):
        template = "genshi:tw2.devtools.templates.wb_welcome"


class BrowseWidget(twc.Widget):
    id = None
    template = 'genshi:tw2.devtools.templates.wb_widget'
    name = twc.Variable()
    widget = twc.Variable()
    params = twc.Variable()
    child_params = twc.Variable()
    demo = twc.Variable()
    source = twc.Variable()
    rst2html = rst2html

    def prepare(self):
        super(BrowseWidget, self).prepare()
        if self.value:
            self.name, self.widget, self.demo, self.source = self.value

            if self.source:
                self.resources.extend([
                    tw2.jquery.jquery_js,
                    tw2.jqplugins.ui.jquery_ui_js,
                    tw2.jqplugins.ui.jquery_ui_css,
                    twc.JSLink(modname=__name__,
                               filename='static/js/source.js')
                ])

            if getattr(self.widget, '_hide_docs', False) and self.demo:
                self.demo.resources.extend([
                    tw2.jquery.jquery_js,
                    twc.JSLink(modname=__name__,
                               filename='static/js/browser.js')])
            self.params = sorted(self.widget._params.values(), key=lambda p: p._seq)
            self.child_params = [p for p in self.widget._all_params.values()
                                            if p.child_param and not p.internal]
            self.child_params.sort(key=lambda p: p._seq)
            req_prm = [p.name for p in self.params if p.default is twc.Required]
            if self.demo:
                self.demo = self.demo(id='demo', parent=self.__class__).req()
                self.demo.prepare()
            elif not req_prm or req_prm == ['id']: # auto demo
                self.demo = self.widget(id='demo', parent=self.__class__).req()
                self.demo.prepare()
            else:
                self.demo = None

class ModuleMissing(Exception):
    pass

class Module(WbPage):
    def fetch_data(self, req):
        self.child.module = req.GET['module']
        self.child.child.module = req.GET['module']

    class child(twc.DisplayOnlyWidget):
        template = 'genshi:tw2.devtools.templates.wb_module'
        rst2html = rst2html

        def prepare(self):
            try:
                sample_module = __import__(self.module + '.samples', fromlist=[''])
                if 'page_options' in dir(sample_module):
                    for k,v in sample_module.page_options.items():
                        setattr(self, k, v)
            except ImportError, e:
                warnings.warn("ImportError for '%s': %s" % (
                    self.module, str(e)))
            twc.DisplayOnlyWidget.prepare(self)

        class child(twc.RepeatingWidget):
            module = twc.Param('module to display')
            child = BrowseWidget

            def _load_ep(self, module):
                for ep in pr.iter_entry_points('tw2.widgets'):
                    if ep.module_name == module:
                        return ep.load()
                raise ModuleMissing(module)

            def _get_widgets(self, module=None, modname=None):
                if not module:
                    module = self._load_ep(modname)
                widgets = []
                for attr in dir(module):
                    widget = getattr(module, attr)
                    if isinstance(widget, twc.widgets.WidgetMeta):
                        widgets.append((attr, widget))
                widgets.sort(key=lambda t: t[1]._seq)
                return widgets

            def prepare(self):
                demo_for, source_for = {}, {}
                try:
                    sample_module = __import__(self.module + '.samples', fromlist=[''])
                except ImportError, e:
                    warnings.warn("ImportError for '%s': %s" % (
                        self.module, str(e)))
                else:
                    samples = self._get_widgets(sample_module)
                    for n,s in samples:
                        df = s.__dict__.get('demo_for', s.__mro__[1])
                        demo_for[df] = s
                        source_for[df] = prepare_source(s)

                self.mod = self._load_ep(self.module)
                widgets = self._get_widgets(self.mod)
                self.parent.mod = self.mod
                self.value = [(n, w, demo_for.get(w), source_for.get(w))
                              for n, w in widgets]
                twc.RepeatingWidget.prepare(self)


class Validators(WbPage):
    class child(twc.RepeatingWidget):
        def prepare(self):
            self.value = sorted([ep for ep in pr.iter_entry_points('tw2.widgets')], key=lambda e: e.module_name)
            twc.RepeatingWidget.prepare(self)
        class child(twc.Widget):
            template = 'genshi:tw2.devtools.templates.wb_validator'
            rst2html = rst2html
            def prepare(self):
                twc.Widget.prepare(self)
                vd = self.value.load()
                self.validators = [getattr(vd, v) for v in dir(vd)
                            if isinstance(getattr(vd, v), twc.validation.ValidatorMeta)]


class WbCommand(pc.Command):
    parser = pc.Command.standard_parser(verbose=False)
    parser.add_option('-p', '--port',
                      dest='port',
                      help="Specify the port to listen on",
                      default='8000')
    parser.add_option('-l', '--listen',
                      dest='host',
                      help="Specify the address to listen on",
                      default="127.0.0.1")

    parser.add_option('-r', '--enable-repo-metadata',
                      action='store_true', dest='enable_repo_metadata',
                      default=False, help="Enable source repo metadata")
    parser.add_option('-i', '--enable-pypi-metadata',
                      action='store_true', dest='enable_pypi_metadata',
                      default=False, help="Enable pypi package metadata")

    parser.add_option('-t', '--use-threadpool', action='store_true',
                      dest='use_threadpool', default=False,
                      help="Server requests from a pool of worker threads")
    parser.add_option('-w', '--threadpool-workers',
                      dest='threadpool_workers', default=10,
                      help="Number of worker threads to create when " +
                      "``use_threadpool`` is true")
    parser.add_option('-s', '--request-queue-size',
                      dest='request_queue_size', default=5,
                      help="specifies the maximum number of queued connections")


    def command(self):
        WbPage.enable_repo_metadata = self.options.enable_repo_metadata
        WbPage.enable_pypi_metadata = self.options.enable_pypi_metadata
        tw2.devtools.dev_server(
            host=self.options.host, port=self.options.port,
            use_threadpool=self.options.use_threadpool,
            threadpool_workers=self.options.threadpool_workers,
            request_queue_size=self.options.request_queue_size,
        )
    group_name = 'tw2'
    summary = 'Browse available ToscaWidgets'
    min_args = 0
    max_args = 0

if __name__ == '__main__':
    tw2.devtools.dev_server()
