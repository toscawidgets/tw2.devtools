import os
import datetime
from pkg_resources import get_distribution, require
require("PasteScript")
from paste.script.templates import Template, var

class ToscaWidgetsTemplate(Template):
    _template_dir = os.path.join(get_distribution('tw2.devtools').location,
                                 'tw2', 'paste_templates', 'widget_template')
    summary = "ToscaWidgets widget"

    vars = [
        var('widget_name', 'Name of the widget package (tw2.xxx)'),
        ]

    def run(self, command, output_dir, vars):
        vars['package'] = vars['widget_name'] or vars['package']
        super(ToscaWidgetsTemplate, self).run(command, output_dir, vars)
