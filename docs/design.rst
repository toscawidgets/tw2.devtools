Design Documentation
--------------------

This document discusses the design objectives and implementation of ToscaWidgets 2. It is intended to be reference documentation for both developers and users of widgets, and for developers of ToscaWidgets itself. New users should start with the tutorial.


General Considerations
======================

**Packaging**

ToscaWidgets comes in two main packages:

 * tw.core - the core functionality needed to use widgets in an app
 * tw.devtools - documentation, unit tests, widget browser, library template, resource collator

The idea is that only tw.core needs to be installed on a server. It has minimal dependencies, while tw.devtools has more, e.g. sphinx.

Widget library packages follow the same naming convention, e.g. tw.forms.

**Framework Interface**

ToscaWidgets is designed to be standalone WSGI middeware and not have any framework interactions. However, when using ToscaWidgets with a framework, there are some configuration settings that need to be consistent with the framework, for correct interaction.

There are some framework specific hooks, which align configuration with the frameworks configuration. Some framework hooks (e.g. TurboGears) automatically stack the middleware.

**Request-Local Storage**

ToscaWidgets needs access to request-local storage. In particular, it's important that the middleware sees the request-local information that was set when a widget is instatiated, so that resources are collected correctly.

The function tw.core.request_local returns a dictionary that is local to the current request. Multiple calls in the same request always return the same dictionary. The default implementation of request_local is a thread-local system, which the middleware clears before and after each request.

In some situations thread-local is not appropriate, e.g. twisted. In this case the application will need to monkey patch request_local to use appropriate request_local storage.

**Thread Safety**

ToscaWidgets is designed to support thread-safe usage, with no internal locks. To support this, Widget classes must not be modified after they are defined, and Widget instances must only be used in a single thread.

**pkg_resources**

tw.core aims to take advantage of pkg_resources where it is available, but not to depend on it. This allows tw.core to be used on Google App Engine. pkg_resources is used in two places:

 * In ResourcesApp, to serve resources from modules, which may be zipped eggs. If pkg_resources is not available, this uses a simpler system that does not support zipped eggs.
 * In EngingeManager, to load a templating engine from a text string, e.g. "genshi". If pkg_resources is not available, this uses a simple, built-in mapping that covers the most common template engines.

**Testing**

ToscaWidgets has quite comprehensive unit tests. To run the tests, in ``tw.devtools/tests`` run ``nosetests``.


Configuration
=============

In general, ToscaWidgets configuration is done on the middleware instance. At the beginning of each request, the middleware stores a reference to itself in request-local storage. So, during a request, a widget can consult request-local storage, and get the configuration for the middleware active in that request. This allows multiple applications to use ToscaWidgets, with different configurations, in a single Python environment.

Configuration is passed as keyword arguments to the middleware constructor. The available parameters are:

.. autoclass:: tw.core.middleware.Config

However, some configuration values must be done on a global basis. These are:

    `compound_id_separator`
        (default: ':')


Middleware
==========




Widget Class
============

.. autoclass:: tw.core.widgets.Widget


Identifier
~~~~~~~~~~

In general, a widget needs to have an identifier. Without an id, it cannot participate in value propagation or validation, and it does not get an id= attribute. For widgets with an id, a compound id is generated for the id= attribute, by joining it's parent and all ancestors' ids. The default separator is colon (:), resulting in compound ids like "form:sub_form:field".

There are some exceptions to this:

 * Some widgets do not need an id (e.g. Label, Spacer) and provide a default id of None.
 * The child of a RepeatingWidget must not have an id. The repetition is used instead to generate compound  ids.
 * DisplayOnlyWidget takes the id from its child, but uses None for generating compound ids.
 * If a child of a CompoundWidget is also a CompoundWidget, and has no id, this causes the children of the child CompoundWidget to be merged with the children of the parent CompoundWidget. This also works with a DisplayOnlyWidget between the two CompoundWidgets.

Parameters
~~~~~~~~~~

The parameters are how the user of the widget controls its display and behaviour. Parameters exist primarily for documentation purposes, although they do have some run-time effects. When creating widgets, it's important to decide on a convenient set of parameters for the user of the widget, and to document these.

A parameter definition looks like this::

    class MyTextField(tw.Widget):
        size = tw.Param('The size of the field', default=30)
        validator = tw.MaxLength()
        highlight = tw.Variable('Region to highlight')

In this case, :class:`TextField` gets all the parameters of its base class, :class:`tw.core.widget` and defines a new parameter - :attr:`size`. A widget can also override parameter in its base class, either with another :class:`tw.core.Param` instance, or a new default value.

.. autoclass:: tw.core.Param
.. autoclass:: tw.core.Variable
.. autoclass:: tw.core.ChildParam
.. autoclass:: tw.core.ChildVariable


Code Hooks
~~~~~~~~~~

Subclasses of Widget can override the following methods. It is not recommended to override any other methods, e.g. display, validate, __init__.

.. automethod:: tw.core.widgets.BaseWidget.post_define
.. automethod:: tw.core.widgets.BaseWidget.post_init


Widget Hierarchy
================

Widgets can be arranged in a hierarchy. This is useful for applications like layouts, where the layout will be a parent widget and fields will be children of this. There are four roles a widget can take in the hierarchy, depending on the base class used:

.. autoclass:: tw.core.LeafWidget
.. autoclass:: tw.core.CompoundWidget
.. autoclass:: tw.core.RepeatingWidget
.. autoclass:: tw.core.DisplayOnlyWidget

An important feature of the hierarchy is value propagation. When the value is set for a compound or repeating widget, this causes the value to be set for the child widgets. In general, a leaf widget takes a scalar type as a value, a compound widget takes a dict or an  object, and a repeating widget takes a list.

The hierarchy also affects the generation of compound ids, and validation.


Template
========

Every widget has a template, this is core to the widget concept. ToscaWidgets aims to support any templating engine that support the ``buffet`` interface, which is an attempt by the TurboGears project to create a standard interface for template libraries. In practice, there are a few differences between template engines that the buffet interface does not standardise. So, ToscaWidgets has some template-language hooks, and support is primarily for: Genshi, Mako, Kid and Cheetah.

The :attr:`template` parameter takes the form ``engine_name:template_path``. The ``engine_name`` is the name that the template engine defines in the ``python.templating.engines`` entry point, e.g. ``genshi`` or ``mako``. Specifying the engine name is compulsory, unlike previous versions of ToscaWidgets. The ``template_path`` is a string the engine can use to locate the template; usually this is dot-notation that mimics the semantics of Python's import statement, e.g. ``myapp.templates.mytemplate``.


.. automethod:: tw.core.widgets.Widget.display
.. autoclass:: tw.core.template.EngineManager


Resources
=========

Widgets often need to access resources, such as JavaScript or CSS files. A key feature of widgets is the ability to automatically serve such resources, and insert links into appropriate sections of the page, e.g. ``<HEAD>``. There are several parts to this:

 * Widget subclasses can define resources they use
 * When a Widget is instantiated, it registers resources in request-local storage
 * The resource injection middleware detects resources in request-local storage, and rewrites the generated page to include appropriate links.
 * The resource server middleware serves static files used by widgets

TBD: removing dupes
Efficiency - merging with parent

Defining Resources
~~~~~~~~~~~~~~~~~~

To define a resource, just add a :class:`tw.core.Resource` subclass to the widget's :attr:`resources` parameter. The following resource types are available:

.. autoclass:: tw.core.CSSLink
.. autoclass:: tw.core.JSLink
.. autoclass:: tw.core.JSSource


Validation
==========

One of the main features of any forms library is the vaidation of form input, e.g checking that an email address is valid, or that a user name is not already taken. If there are validation errors, these must be displayed to the user in a helpful way. Many validation tasks are common, so these should be easy for the developer, while less-common tasks are still possible.

**Conversion**

Validation is also responsible for conversion to and from python types. For example, the DateValidator takes a string from the form and produces a python date object. If it is unable to do this, that is a validation failure.

To keep related functionality together, validators also support coversion from python to string, for display. This should be complete, in that there are no python values that cause it to fail. It should also be precise, in that converting from python to string, and back again, should always give a value equal to the original python value. The converse is not always true, e.g. the string "1/2/2004" may be converted to a python date object, then back to "01/02/2004".

**Validation Errors**

When validation fails, the user should see the invalid values they entered. This is helpful in the case that a field is entered only slightly wrong, e.g. a number entered as "2,000" when commas are not allowed. In such cases, conversion to and from python may not be possible, so the value is kept as a string. Some widgets will not be able to display an invalid value (e.g. selection fields); this is fine, they just have to do the best they can.

When there is an error, whether valid fields could potentially normalise their value, by converting to python and back again. It was decided to use the original value in this case, although this may become a configurable option in the future.

In some cases, validation may encounter a major error, as if the web user has tampered with the HTML source. However, we can never be completely sure this is the case, perhaps they have a buggy browser, or caught the site in the middle of an upgrade. In these cases, validation will produce the most helpful error messages it can, which may just be "Your form submission was received corrupted; please try again."

**Required Fields**

If a field has no value, if defaults to ``None``. It is down to that field's validator to raise an error if the field is required. By default, fields are not required. It was considered to have a dedicated ``Missing`` class, but this was decided against, as ``None`` is already intended to convey the absence of data.

**Security Consideration**

When a widget is redisplayed after a validation failure, it's value is derived from unvalidated user input. So, all widgets must be "safe" for all input values. In practice, this is almost always the case without great care, so widgets are assumed to be safe. If a particular widget is not safe in this way, it must declare... TBD

Using Validators
~~~~~~~~~~~~~~~~

There's two parts to using validators. First, specify validators in the widget definition, like this::

    class RegisterUser(twf.TableForm):
        validator = MyValidator
        name = twf.TextField
        password = twf.PasswordField(validator=twf.StrongPassword(minlen=6))
        confirm_password = twf.PasswordField(validator=twf.MatchField('password'))

You can specify a validator on any widget, either a class or an instance. Using an instance lets you pass parameters to the validator. You can code your own validator by subclassing :class:`tw.core.Validator`. All validators have at least these parameters:

Second, when the form values are submitted, call :meth:`validate` on the outermost widget. Pass this a dictionary of the request parameters. It will call the same method on all contained widgets, and either return the validated data, with all conversions applied, or raise :class:`tw.core.ValidationError`. In the case of a validation failure, it stores the invalid value and an error message on the affected widget, in request-local parameters.

CherryPy code to perform validation looks like this::

    def movie(self, id):
        return movie_template.render(movie=Movie.get(id))

    def save_movie(self, **params):
        try:
            data = movie_form.validate(params)
            # use the validated data here
        except twc.ValidationError:
            return movie_template.render(movie=None)

FormEncode
~~~~~~~~~~

Earlier versions of ToscaWidgets used FormEncode for validation and there are good reasons for this. Some aspects of the design work very well, and FormEncode has a lot of clever validators, e.g. the ability to check that a post code is in the correct format for a number of different countries.

However, there are challenges making FormEncode and ToscaWidgets work together. For example, both libraries store the widget hierarchy internally. This makes implementing some features (e.g. ``strip_name`` and :class:`tw.dynforms.HidingSingleSelectField`) difficult. There are different needs for the handling of unicode, leading ToscaWidgets to override some behaviour. Also, FormEncode just does not support client-side validation, a planned feature of ToscaWidgets 2.

ToscaWidgets 2 does not rely on FormEncode. However, developers can use FormEncode validators for individual fields. The API is compatible in that :meth:`to_python` and :meth:`from_python` are called for conversion, and :class:`formencode.Invalid` is caught.

Implementation
~~~~~~~~~~~~~~

TBD
A two-pass approach is used internally, although this is invisible to the user. When :meth:`Widget.validate` is called (with validate=True), it automatically calls :meth:`Widget.unflatten_params`.

    unflatten_params decodes compound ids - use doc string

Then validate works recursively, using the widget hierarchy

There is a specific :class:`tw.core.Invalid` marker, but this is only seen in a compound/repeating validator, if some of the children have failed validation.


Declarative Instantiation
=========================

Instantiating compound widgets can result in less-than-beautiful code. To help alleviate this, widgets can be defined declaratively, and this is the recommended approach. A definition looks like this::

    class MovieForm(twf.TableForm):
        action = 'save_movie'

        id = twf.HiddenField
        year = twf.TextField
        desc = twf.TextArea(rows=5)

Any class members that are subclasses of Widget become children. All the children get their ``id`` from the name of the member variable. The compound widget itself gets its ``id`` from the class name, but rewritten to, e.g. ``movie_form``.

Inheritence is supported - a subclass gets the children from the base class, plus any defined on the subclass. If there's a name clash, the subclass takes priority. Multiple inheritence resolves ame clashes in a similar way.

Nested declarative definitions can be used, like this::

    class MyForm(twf.Form):
        class child(twf.TableLayout):
            b = twf.TextArea()
            x = twf.Label(text='this is a test')
            c = twf.TextField()

It is possible to define children that have the same name as parameters, using this syntax. However, doing so does prevent a widget overriding a parameter, and defining a child with the same name. This is expected to be a rare issue. However, if necessary, the following workaround can be used::

    class MovieForm(twf.TableForm):
        action = 'save_movie'

        class children(twc.WidgetList):
            action = twf.TextField


Widget Browser
==============

blah

The parameters that are displayed are: all the required parameters, plus non-required parameters that are defined on anything other than the Widget base class. Variables are never shown.


History
=======

Python web widgets were pioneered in TurboGears and many of the key ideas remain. Once the value of widgets was realised, a move was made to create a separate library, this is ToscaWidgets. The key differences are:

 * ToscaWidget is framework independent.
 * Multiple template engines are supported.
 * Resource links are injected by rewriting the page on output.
 * The forms library is separate from the core widget library.
 * The tw namespace exists for widget libraries to be located in.

ToscaWidgets had some success, but did not gain as much usage as hoped, in part due to a lack of documentation in the beginning. Over time, several moves were made to simplify the library. ToscaWidgets 2 is an attempt to simplify widgets even further - at the cost of breaking backward-compatibility. The key differences are:

 * TBD - instance per request
 * In widget libraries, parameters are defined declaratively.
 * Validation is done in the core widget library, and no longer relies on FormEncode.
 * Declarative instantiation of widgets has been made more concise.
 * Framework interfaces are almost completely removed; ToscaWidgets is just a piece of WSGI middleware.

Some minor differences to be aware of:

 * There is no automatic calling of parameters; you must explicitly use :class:`tw.core.Deferred` for this.
 * A widget does not automatically get the ``resources`` from its base class.
 * engine_name is compulsory for templates, and there are no inline templates (yet, may be added later).
 * ToscaWidgets 2 requires Python 2.5
 * tw.api has been removed; just use tw.core
 * The compound ID separator is now a colon (:) and IDs may not contain colons.
 * The toscasidgets simple template engine has been removed.
 * Widget.__call__ is no longer an alias for display, as this causes problems for Cheetah.

In tw.forms
 * name is always identical to id
 * Simpler inheritence tree
