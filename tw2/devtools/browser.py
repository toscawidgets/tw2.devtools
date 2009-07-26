import wsgiref.simple_server as ws, tw2.core as twc
import pkg_resources as pr


class Index(twc.Page):
    template = "genshi:tw2.devtools.templates.wb_index"

class Welcome(twc.Page):
    resources = [twc.CSSLink(modname=__name__, filename='static/tosca.css')]
    template = "genshi:tw2.devtools.templates.wb_welcome"

class List(twc.Page):
    resources = [twc.CSSLink(modname=__name__, filename='static/tosca.css')]
    template = "genshi:tw2.devtools.templates.wb_list"
    modules = twc.Variable()
    def prepare(self):
        super(List, self).prepare()
        self.modules = sorted(ep.module_name
                        for ep in pr.iter_entry_points('tw2.widgets')
                        if not ep.module_name.endswith('.samples'))


class BrowseWidget(twc.Widget):
    id = None
    template = 'genshi:tw2.devtools.templates.wb_widget'
    resources = [twc.CSSLink(modname='tw2.devtools', filename='static/browser.css')]
    name = twc.Variable()
    widget = twc.Variable()
    params = twc.Variable()
    child_params = twc.Variable()
    demo = twc.Variable()

    def prepare(self):
        super(BrowseWidget, self).prepare()
        if self.value:
            self.name, self.widget, self.demo = self.value
            self.params = sorted(self.widget._params.values(), key=lambda p: p._seq)
            self.child_params = [p for p in self.widget._all_params.values()
                                            if p.child_param and not p.internal]
            self.child_params.sort(key=lambda p: p._seq)
            req_prm = [p.name for p in self.params if p.default is twc.Required]
            if self.demo:
                self.demo = self.demo(id='demo', parent=self).req()
                self.demo.prepare()
            elif not req_prm or req_prm == ['id']: # auto demo
                self.demo = self.widget(id='demo', parent=self).req()
                self.demo.prepare()
            else:
                self.demo = None

class ModuleMissing(Exception):
    pass

class Module(twc.Page):
    resources = [twc.CSSLink(modname=__name__, filename='static/tosca.css')]
    template = 'genshi:tw2.devtools.templates.wb_module'
    def fetch_data(self, req):
        self.module = req.GET['module']
        self.child.module = req.GET['module']

    def prepare(self):
        try:
            sample_module = __import__(self.module + '.samples', fromlist=[''])
            if 'page_options' in dir(sample_module):
                for k,v in sample_module.page_options.items():
                    setattr(self, k, v)
        except ImportError:
            pass
        super(Module, self).prepare()

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
            demo_for = {}
            try:
                sample_module = __import__(self.module + '.samples', fromlist=[''])
            except ImportError:
                pass
            else:
                samples = self._get_widgets(sample_module)
                for n,s in samples:
                    df = s.__dict__.get('demo_for', s.__mro__[1])
                    demo_for[df] = s
            self.mod = self._load_ep(self.module)
            widgets = self._get_widgets(self.mod)
            self.parent.mod = self.mod
            self.value = [(n, w, demo_for.get(w)) for n, w in widgets]
            twc.RepeatingWidget.prepare(self)


class Validators(twc.Page):
    title = 'Validators'
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


from paste.script import command as pc

class WbCommand(pc.Command):
    def command(self):
        ws.make_server('', 8000, twc.make_middleware(controller_prefix='/')).serve_forever()
    group_name = 'tw2'
    summary = 'Browse available ToscaWidgets'
    min_args = 0
    max_args = 0
    usage = "then browse to http://localhost:8000/"

    parser = pc.Command.standard_parser(verbose=True)


if __name__ == '__main__':
    ws.make_server('', 8000, twc.make_middleware(controller_prefix='/')).serve_forever()
