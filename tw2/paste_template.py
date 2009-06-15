import os
import datetime
from pkg_resources import get_distribution, require
require("PasteScript")
from paste.script.templates import Template, var

class ToscaWidgetsTemplate(Template):
    _template_dir = os.path.join(get_distribution('ToscaWidgets').location,
                                 'tw', 'paste_templates', 'widget_template')
    summary = "ToscaWidgets widget"

    vars = [
        var('widget_name', 'Name of the widget package (tw.XXX)'),
        var('version', 'Version', default='0.1a0'),
        var('description', 'One-line description of the widget'),
        var('long_description', 'Multi-line description (in reST)'),
        var('author', 'Author name'),
        var('author_email', 'Author email'),
        var('url', 'URL of homepage'),
        var('license_name', 'License name'),
        ]

    def run(self, command, output_dir, vars):
        vars['year'] = str(datetime.datetime.now().year)
        vars['package'] = vars['widget_name'] or vars['package']
        super(ToscaWidgetsTemplate, self).run(command, output_dir, vars)
