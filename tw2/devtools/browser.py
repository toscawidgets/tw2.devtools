from __future__ import print_function

import tw2.core as twc, pkg_resources as pr, docutils.core, os
import tw2.devtools
import tw2.jquery
import tw2.jqplugins.ui
from paste.script import command as pc
from paste.script.serve import _turn_sigterm_into_systemexit

import inspect
import pygments
import subprocess
import sys
import xmlrpclib

import warnings
from . import memoize
import six


class WbPage(twc.Page):
    _no_autoid = True
    resources = [twc.CSSLink(modname=__name__, filename='static/css/reset.css'),
                 twc.CSSLink(modname=__name__, filename='static/css/core.css'),
                 twc.CSSLink(modname=__name__, filename='static/css/grid.css'),
                 twc.CSSLink(modname=__name__, filename='static/css/pygments.css'),
                 twc.DirLink(modname=__name__, filename='static/')]

    template = "genshi:tw2.devtools.templates.wb_page"
    def prepare(self):
        super(WbPage, self).prepare()
        self.modules = sorted(ep.module_name
                        for ep in pr.iter_entry_points('tw2.widgets')
                        if not ep.module_name.endswith('.samples'))
        self.pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')

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

    def prepare(self):
        super(BrowseWidget, self).prepare()
        tw2.jqplugins.ui.set_ui_theme_name('pepper-grinder')
        if self.value:
            self.name, self.widget, self.demo = self.value

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
                try:
                    self.demo = self.demo(id='demo', parent=self.__class__).req()
                    self.demo.prepare()
                except Exception as e:
                    warnings.warn(six.text_type(e))
                    self.demo = None

            elif not req_prm or req_prm == ['id']: # auto demo
                try:
                    self.demo = self.widget(id='demo', parent=self.__class__).req()
                    self.demo.prepare()
                except Exception as e:
                    warnings.warn(six.text_type(e))
                    self.demo = None
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

        def prepare(self):
            try:
                sample_module = __import__(self.module + '.samples', fromlist=[''])
                if 'page_options' in dir(sample_module):
                    for k,v in sample_module.page_options.items():
                        setattr(self, k, v)
            except ImportError as e:
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
                except ImportError as e:
                    warnings.warn("ImportError for '%s': %s" % (
                        self.module, str(e)))
                else:
                    samples = self._get_widgets(sample_module)
                    for n,s in samples:
                        df = s.__dict__.get('demo_for', s.__mro__[1])
                        demo_for[df] = s

                self.mod = self._load_ep(self.module)
                widgets = self._get_widgets(self.mod)
                self.parent.mod = self.mod
                self.value = [(n, w, demo_for.get(w))
                              for n, w in widgets]
                twc.RepeatingWidget.prepare(self)


class Validators(WbPage):
    class child(twc.RepeatingWidget):
        def prepare(self):
            self.value = sorted([ep for ep in pr.iter_entry_points('tw2.widgets')], key=lambda e: e.module_name)
            twc.RepeatingWidget.prepare(self)
        class child(twc.Widget):
            template = 'genshi:tw2.devtools.templates.wb_validator'

            def prepare(self):
                twc.Widget.prepare(self)
                vd = self.value.load()
                self.validators = [getattr(vd, v) for v in dir(vd)
                            if isinstance(getattr(vd, v), twc.validation.ValidatorMeta)]


class WbCommand(pc.Command):
    parser = pc.Command.standard_parser(verbose=True)
    parser.add_option('-p', '--port',
                      dest='port',
                      help="Specify the port to listen on",
                      default='8000')
    parser.add_option('-l', '--listen',
                      dest='host',
                      help="Specify the address to listen on",
                      default="127.0.0.1")
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

    parser.add_option('--reload',
                      dest='reload',
                      action='store_true',
                      help="Use auto-restart file monitor")
    parser.add_option('--reload-interval',
                      dest='reload_interval',
                      default=1,
                      help="Seconds between checking files (low "
                      "number can cause significant CPU usage)")

    _reloader_environ_key = 'PYTHON_RELOADER_SHOULD_RUN'



    def restart_with_reloader(self):
        """ Copy/pasted from paste.script.server. """
        self.restart_with_monitor(reloader=True)

    def restart_with_monitor(self, reloader=False):
        """ Copy/pasted from paste.script.server. """

        if self.verbose > 0:
            if reloader:
                print('Starting subprocess with file monitor')
            else:
                print('Starting subprocess with monitor parent')
        while 1:
            args = [self.quote_first_command_arg(sys.executable)] + sys.argv
            new_environ = os.environ.copy()
            if reloader:
                new_environ[self._reloader_environ_key] = 'true'

            proc = None
            try:
                try:
                    _turn_sigterm_into_systemexit()
                    proc = subprocess.Popen(args, env=new_environ)
                    exit_code = proc.wait()
                    proc = None
                except KeyboardInterrupt:
                    print('^C caught in monitor process')
                    if self.verbose > 1:
                        raise
                    return 1
            finally:
                if (proc is not None
                    and hasattr(os, 'kill')):
                    import signal
                    try:
                        os.kill(proc.pid, signal.SIGTERM)
                    except (OSError, IOError):
                        pass

            if reloader:
                # Reloader always exits with code 3; but if we are
                # a monitor, any exit code will restart
                if exit_code != 3:
                    return exit_code
            if self.verbose > 0:
                print('-'*20, 'Restarting', '-'*20)


    def command(self):
        if self.options.reload:
            if os.environ.get(self._reloader_environ_key):
                from paste import reloader
                if self.verbose > 1:
                    print('Running reloading file monitor')

                reloader.install(int(self.options.reload_interval))

            else:
                self.restart_with_reloader()

        if self.verbose > 0:
            if hasattr(os, 'getpid'):
                msg = 'Starting server in PID %i.' % os.getpid()
            else:
                msg = 'Starting server.'
            print(msg)

        try:
            self.serve()
        except (SystemExit, KeyboardInterrupt) as e:
            if self.verbose > 1:
                raise
            if str(e):
                msg = ' '+str(e)
            else:
                msg = ''
            print('Exiting%s (-v to see traceback)' % msg)


    def serve(self):
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
