from __future__ import print_function

import tw2.core as twc, pkg_resources as pr, docutils.core, os
import tw2.devtools
import tw2.jquery
import tw2.jqplugins.ui

import gearbox.commands.serve

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
    title = "The Toscawidgets2 Widget Browser"
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


TW2_DEVTOOLS_CONFIG_FILE = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'browser_config.ini',
)

class WbCommand(gearbox.commands.serve.ServeCommand):

    def get_description(self):
        return 'Serves the ToscaWidgets2 Widget Browser'

    def get_parser(self, prog_name):
        parser = super(WbCommand, self).get_parser(prog_name)

        # Hack the --config-file option to return *our* config file by default.
        for i in range(len(parser._actions)):
            if parser._actions[i].dest == 'config_file':
                parser._actions[i].default = TW2_DEVTOOLS_CONFIG_FILE

        return parser

if __name__ == '__main__':
    tw2.devtools.dev_server()
