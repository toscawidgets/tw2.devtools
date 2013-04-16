import docutils.core
import genshi.input as gsi
import inspect
import os
import pygments.lexers
import pygments.formatters
import warnings
import webhelpers.html

import tw2.core as twc
import tw2.core.templating as twt
import tw2.jqplugins.ui

from six.moves import filter


def prepare_source(s):
    try:
        source = inspect.getsource(s.mro()[1])
    except IOError as e:
        warnings.warn(repr(s) + " : " + str(e))
        return ""

    html_args = {'full': False}
    return pygments.highlight(
        source,
        pygments.lexers.PythonLexer(),
        pygments.formatters.HtmlFormatter(**html_args)
    )


def prepare_template(s):
    template_name = s.template

    # Determine the engine name
    if not s.inline_engine_name:
        engine_name = twt.get_engine_name(template_name)
    else:
        engine_name = s.inline_engine_name

    # Load the template source
    source = twt.get_source(engine_name, template_name, s.inline_engine_name)

    lexer_lookup = dict(
        # Genshi
        genshi=pygments.lexers.GenshiLexer,
        genshi_abs=pygments.lexers.GenshiLexer,

        # Kajiki is meant to be 'just like genshi'
        kajiki=pygments.lexers.GenshiLexer,

        # Mako
        mako=pygments.lexers.MakoLexer,

        # Jinja
        jinja=pygments.lexers.DjangoLexer,
        jinja2=pygments.lexers.DjangoLexer,

        # We just have to go out on a limb for this one...
        chameleon=pygments.lexers.GenshiLexer,
    )

    html_args = {'full': False}
    return pygments.highlight(
        source,
        lexer_lookup[engine_name](),
        pygments.formatters.HtmlFormatter(**html_args)
    )


def rst2html(rst):
    html = docutils.core.publish_string(
        rst or '',
        writer_name='html',
        settings_overrides={
            'template': os.path.dirname(__file__) + '/rststub.txt'
        }
    )
    html = html.replace('<blockquote>', '').replace('</blockquote>', '')
    return gsi.HTML(html.decode('utf-8'))


def _make_demo(widget):
    if widget.demo:
        try:
            return dict(label="Demo", content=widget.demo.display())
        except Exception as e:
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
    if widget.demo and hasattr(widget.demo, 'template'):
        return dict(label="Template", content=prepare_template(widget.demo))

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
