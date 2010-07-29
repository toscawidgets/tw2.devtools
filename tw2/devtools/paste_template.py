import os, pkg_resources as pr, paste.script.templates as pst
pr.require("PasteScript")

class ToscaWidgetsTemplate(pst.Template):
    _template_dir = os.path.join(pr.get_distribution('tw2.devtools').location,
                                 'tw2', 'paste_templates', 'widget_template')
    summary = "ToscaWidgets widget"

    vars = [
        pst.var('widget_name', 'Name of the widget package (tw2.xxx)'),
    ]

    def run(self, command, output_dir, vars):
        vars['package'] = vars['widget_name'] or vars['package']
        super(ToscaWidgetsTemplate, self).run(command, output_dir, vars)

    def check_vars(self, vars, cmd):
        if '.' in vars['project']:
            [v for v in self.vars if v.name == 'widget_name'][0].default = vars['project'].split('.')[1]
        return super(ToscaWidgetsTemplate, self).check_vars(vars, cmd)
