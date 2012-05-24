
import docutils.core
import genshi.input as gsi
import inspect
import os
import pygments.lexers
import pygments.formatters
import warnings
import webhelpers.html

import tw2.core as twc
import tw2.jqplugins.ui


def prepare_source(s):
    try:
        source = inspect.getsource(s.mro()[1])
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


def rst2html(rst):
    html = docutils.core.publish_string(
        rst or '',
        writer_name='html',
        settings_overrides={
            'template': os.path.dirname(__file__) + '/rststub.txt'
        }
    )
    html = html.replace('<blockquote>', '').replace('</blockquote>', '')
    return gsi.HTML(html)


def _make_demo(widget):
    if widget.demo:
        try:
            return dict(label="Demo", content=widget.demo.display())
        except Exception, e:
            warnings.warn("%r - %r" % (widget.demo, e))

    return None


def _make_docs(widget):
    widget = widget.widget
    if getattr(widget, '__doc__', None):
        return dict(label="Documentation", content=rst2html(widget.__doc__))

    return None


def _make_params(widget):
    def include(p):
        return not (
            p.internal or
            p.default is twc.Required or
            p.defined_on == 'Widget'
        )

    params = filter(include, widget.params)

    if not params:
        return None

    content = "<ul>"
    for p in params:
        content += "<li>%s<ul><li>%s</li></ul></li>" % (p.name, p.description)

    content += "</ul>"

    return dict(label="Parameters", content=content)


def _make_source(widget):
    if widget.demo:
        return dict(label="Source", content=prepare_source(type(widget.demo)))

    return None


def _make_tmpl(widget):
    # TODO -- get template once tw2.core is ready.
    #return dict(label="Template", content="awesome")
    return None

funcs = [_make_demo, _make_docs, _make_params, _make_source, _make_tmpl]


def make_tabs(widget):
    _items = [func(widget) for func in funcs]
    _items = filter(lambda item: item, _items)

    if not _items:
        return ""

    class Tabs(tw2.jqplugins.ui.TabsWidget):
        id = widget.compound_id.replace(':', '-') + "-tabs"
        items = _items

    return webhelpers.html.literal(Tabs.display())
