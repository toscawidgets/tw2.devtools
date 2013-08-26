from __future__ import print_function

import sys
import pprint
import pstats
import cProfile

import pkg_resources
pkg_resources.require('Mako')

try:
    MSG = sys.argv[1]
except IndexError:
    MSG = ''
VERSION = pkg_resources.get_distribution('ToscaWidgets').version
NCALLS = 20
PRINT_CALLERS = False

try:
    # Support >= 0.8
    from tw.api import Widget, WidgetsList
    from tw.forms import *
    from tw.forms.samples import AddUserForm
except ImportError:
    # Support < 0.8
    from toscawidgets.api import Widget, WidgetsList
    from toscawidgets.widgets.forms import *
    from toscawidgets.widgets.forms.samples import AddUserForm

FormField.engine_name = "mako"

data = {'a':'foooo', 'b':'bar',
        'c':[{'a':'foooo', 'b':'bar'},{'a':'foooo', 'b':'bar'}]}

class TestFieldSet(TableFieldSet):
    class fields(WidgetsList):
        a = TextField()
        b = TextField()
class TestForm(TableForm):
    class fields(WidgetsList):
        a = TextField()
        b = TextField()
        c = FormFieldRepeater(widget=TestFieldSet())

def print_stats(title, func, *args, **kw):
    print(title)
    prof = cProfile.Profile()
    def _loop():
        for i in range(NCALLS):
            func(*args, **kw)
    prof.runcall(_loop)
    stats = pstats.Stats(prof)
    #pprint.pprint(stats.get_sort_arg_defs())
    stats = stats.strip_dirs().sort_stats('time', 'call')\
        .print_stats(50)
    if PRINT_CALLERS:
        stats.print_callers(5)


### Start profiling output

print("*"*78)
print("Profiling ToscaWidgets %s in with NCALLS = %d" % (VERSION, NCALLS))
if MSG: print(MSG)

print("*"*78)
print_stats("Widget initialization", Widget, "test_widget")
w = Widget("test_widget")
print_stats("Widget.prepare_dict", w.prepare_dict, "value", {})

print("*"*78)
print_stats("TestForm initialization", TestForm, "test_widget")
w = TestForm("test_widget")
w.display() # preload template
print_stats("TestForm.display", w.display, data)

print("*"*78)
print_stats("AddUserForm initialization", AddUserForm, "test_widget")
w = AddUserForm("test_widget")
w.display() # preload template
print_stats("AddUserForm.display", w.display, data)

try:
    from tw.api import disable_runtime_checks
except ImportError:
    # disable_runtime_checks is only available since 0.9.3dev_20080610
    pass
else:
    print("*"*78)
    print("Disabling runtime checks")
    disable_runtime_checks()
    print("*"*78)
    print_stats("AddUserForm initialization (without checks)", AddUserForm, "test_widget")
    w = AddUserForm("test_widget")
    w.display() # preload template
    print_stats("AddUserForm.display (without checks)", w.display, data)
