Widget Overview
===============

The main purpose of a widget is to display a functional control within an HTML page. A widget has a template to generate its own HTML, and a set of parameters that control how it will be displayed. It can also reference resources - JavaScript or CSS files that support the widget.

When defining Widgets, some parameters with be static - they will stay constant for the whole lifetime of the application. Some parameters are dynamic - they may change for every request. To ensure thread-safety, a separate widget instance is created for every request, and dynamic parameters are only set on an instance. Static parameters are set by subclassing a widget. For example::

    # Initialisation
    class MyWidget(Widget):
        id = 'myid'

    # In a request
    my_widget = MyWidget.req()
    my_widget.value = 'my value'

To make initialisation more concise, the ``__new__`` method on ``Widget`` is overriden, so it creates subclasses, rather than instances. The following code is equivalent to that above::

    # Initialisation
    MyWidget = Widget(id='myid')

In practice, you will rarely need to explictly create an instance, using ``req()``. If the ``display`` or ``validate`` methods are called on a Widget class, they automatically create an instance. For example, the following are equivalent::

    # Explicit creation
    my_widget = MyWidget.req()
    my_widget.value = 'my value'
    my_widget.display()

    # Implicit creation
    MyWidget.display(value='my value')


Parameters
~~~~~~~~~~

The parameters are how the user of the widget controls its display and behaviour. Parameters exist primarily for documentation purposes, although they do have some run-time effects. When creating widgets, it's important to decide on a convenient set of parameters for the user of the widget, and to document these.

A parameter definition looks like this::

    import tw2.core as twc
    class MyTextField(twc.Widget):
        size = twc.Param('The size of the field', default=30)
        validator = twc.LengthValidator(max=30)
        highlight = twc.Variable('Region to highlight')

In this case, :class:`TextField` gets all the parameters of its base class, :class:`tw2.core.widget` and defines a new parameter - :attr:`size`. A widget can also override parameter in its base class, either with another :class:`tw2.core.Param` instance, or a new default value.

.. autoclass:: tw2.core.Param
.. autoclass:: tw2.core.Variable
.. autoclass:: tw2.core.ChildParam
.. autoclass:: tw2.core.ChildVariable


Code Hooks
~~~~~~~~~~

Subclasses of Widget can override the following methods. It is not recommended to override any other methods, e.g. display, validate, __init__.

.. automethod:: tw2.core.widgets.Widget.post_define
.. automethod:: tw2.core.widgets.Widget.prepare


Widget Hierarchy
================

Widgets can be arranged in a hierarchy. This is useful for applications like layouts, where the layout will be a parent widget and fields will be children of this. There are four roles a widget can take in the hierarchy, depending on the base class used:

.. autoclass:: tw2.core.Widget
.. autoclass:: tw2.core.CompoundWidget
.. autoclass:: tw2.core.RepeatingWidget
.. autoclass:: tw2.core.DisplayOnlyWidget

**Value Propagation**

An important feature of the hierarchy is value propagation. When the value is set for a compound or repeating widget, this causes the value to be set for the child widgets. In general, a leaf widget takes a scalar type as a value, a compound widget takes a dict or an  object, and a repeating widget takes a list.

The hierarchy also affects the generation of compound ids, and validation.

**Identifier**

In general, a widget needs to have an identifier. Without an id, it cannot participate in value propagation or validation, and it does not get an id= attribute. For widgets with an id, a compound id is generated for the id= attribute, by joining it's parent and all ancestors' ids. The default separator is colon (:), resulting in compound ids like "form:sub_form:field".

There are some exceptions to this:

 * Some widgets do not need an id (e.g. Label, Spacer) and provide a default id of None.
 * The child of a RepeatingWidget must not have an id. The repetition is used instead to generate compound  ids.
 * DisplayOnlyWidget takes the id from its child, but uses None for generating compound ids. TBD: not quite true now
 * If a child of a CompoundWidget is also a CompoundWidget, and has no id, this causes the children of the child CompoundWidget to be merged with the children of the parent CompoundWidget. This also works with a DisplayOnlyWidget between the two CompoundWidgets.


Template
========

Every widget has a template, this is core to the widget concept. ToscaWidgets aims to support any templating engine that support the ``buffet`` interface, which is an attempt by the TurboGears project to create a standard interface for template libraries. In practice, there are a few differences between template engines that the buffet interface does not standardise. So, ToscaWidgets has some template-language hooks, and support is primarily for: Genshi, Mako, Kid and Cheetah.

The :attr:`template` parameter takes the form ``engine_name:template_path``. The ``engine_name`` is the name that the template engine defines in the ``python.templating.engines`` entry point, e.g. ``genshi`` or ``mako``. Specifying the engine name is compulsory, unlike previous versions of ToscaWidgets. The ``template_path`` is a string the engine can use to locate the template; usually this is dot-notation that mimics the semantics of Python's import statement, e.g. ``myapp.templates.mytemplate``.

.. autoclass:: tw2.core.template.EngineManager


Resources
=========

Widgets often need to access resources, such as JavaScript or CSS files. A key feature of widgets is the ability to automatically serve such resources, and insert links into appropriate sections of the page, e.g. ``<HEAD>``. There are several parts to this:

 * Widgets can define resources they use, using the :attr:`resources` parameter.
 * When a Widget is displayed, it registers resources in request-local storage
 * The resource injection middleware detects resources in request-local storage, and rewrites the generated page to include appropriate links.
 * The resource server middleware serves static files used by widgets

Defining Resources
~~~~~~~~~~~~~~~~~~

To define a resource, just add a :class:`tw2.core.Resource` subclass to the widget's :attr:`resources` parameter. The following resource types are available:

.. autoclass:: tw2.core.CSSLink
.. autoclass:: tw2.core.JSLink
.. autoclass:: tw2.core.JSSource


Middleware
==========

The WSGI middleware has three functions:

 * Request-local storage
 * Configuration
 * Resource injection

**Configuration**

In general, ToscaWidgets configuration is done on the middleware instance. At the beginning of each request, the middleware stores a reference to itself in request-local storage. So, during a request, a widget can consult request-local storage, and get the configuration for the middleware active in that request. This allows multiple applications to use ToscaWidgets, with different configurations, in a single Python environment.

Configuration is passed as keyword arguments to the middleware constructor. The available parameters are:

.. autoclass:: tw2.core.middleware.Config

However, some configuration values must be done on a global basis. These are:

    `compound_id_separator`
        (default: ':')


Declarative Instantiation
=========================

Instantiating compound widgets can result in less-than-beautiful code. To help alleviate this, widgets can be defined declaratively, and this is the recommended approach. A definition looks like this::

    class MovieForm(twf.TableForm):
        action = 'save_movie'

        id = twf.HiddenField()
        year = twf.TextField()
        desc = twf.TextArea(rows=5)

Any class members that are subclasses of Widget become children. All the children get their ``id`` from the name of the member variable. Note: it is important that all children are defined like ``id = twf.HiddenField()`` and not ``id = twf.HiddenField``. Otherwise, the order of the children will not be preserved.

It is possible to define children that have the same name as parameters, using this syntax. However, doing so does prevent a widget overriding a parameter, and defining a child with the same name. If you need to do this; you will need to avoid the declarative style and specify childen explicitly.

**Nesting and Inheritence**

Nested declarative definitions can be used, like this::

    class MyForm(twf.Form):
        class child(twf.TableLayout):
            b = twf.TextArea()
            x = twf.Label(text='this is a test')
            c = twf.TextField()

Inheritence is supported - a subclass gets the children from the base class, plus any defined on the subclass. If there's a name clash, the subclass takes priority. Multiple inheritence resolves ame clashes in a similar way.

**Layouts**

Without layouts, double nesting of classes would often be necessary, e.g.::

    class MyForm(twf.Form):
        class child(twf.TableLayout):
            b = twf.TextArea()

Specifying a layout for a :class:`RepeatingWidget` or :class:`DisplayOnlyWidget` sets the child to the layout, and adds childen of the first class to the layout. The following is equivalent to the definition above::

    class MyForm(twf.Form):
        layout = twf.TableLayout
        b = twf.TextArea()

And this is used by classes like :class:`TableForm` and :class:`TableFieldSet` to allow the user more concise widget definitions::

    class MyForm(twf.TableForm):
        b = twf.TextArea()


General Considerations
======================

**Request-Local Storage**

ToscaWidgets needs access to request-local storage. In particular, it's important that the middleware sees the request-local information that was set when a widget is instatiated, so that resources are collected correctly.

The function tw2.core.request_local returns a dictionary that is local to the current request. Multiple calls in the same request always return the same dictionary. The default implementation of request_local is a thread-local system, which the middleware clears before and after each request.

In some situations thread-local is not appropriate, e.g. twisted. In this case the application will need to monkey patch request_local to use appropriate request_local storage.

**pkg_resources**

tw2.core aims to take advantage of pkg_resources where it is available, but not to depend on it. This allows tw2.core to be used on Google App Engine. pkg_resources is used in two places:

 * In ResourcesApp, to serve resources from modules, which may be zipped eggs. If pkg_resources is not available, this uses a simpler system that does not support zipped eggs.
 * In EngingeManager, to load a templating engine from a text string, e.g. "genshi". If pkg_resources is not available, this uses a simple, built-in mapping that covers the most common template engines.

**Framework Interface**

ToscaWidgets is designed to be standalone WSGI middeware and not have any framework interactions. However, when using ToscaWidgets with a framework, there are some configuration settings that need to be consistent with the framework, for correct interaction. Future vesions of ToscaWidgets may include framework-specific hooks to automatically gather this configuration.

