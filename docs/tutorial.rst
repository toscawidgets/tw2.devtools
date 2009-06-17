Tutorial
========

This tutorial will show you how to get ToscaWidgets 2 working with a WSGI application. You need to install tw2.core, tw2.devtools and tw2.forms, from the Mercurial repositories::

    hg clone http://bitbucket.org/paj/tw2core/ tw2.core
    hg clone http://bitbucket.org/paj/tw2devtools/ tw2.devtools
    hg clone http://bitbucket.org/paj/tw2forms/ tw2.forms

You need to run ``python setup.py develop`` for each repository.

To check the install worked, we will try to run the widget browser. Issue ``paster twbrowser`` then browse to http://localhost:8000/. You should see the widget browser, like this:

.. image:: tut0.png


Simple WSGI Application
-----------------------

We'll start by creating a simple WSGI application, using WebOB. Create ``myapp.py`` with the following::

    import webob as wo, wsgiref.simple_server as wrs, os

    def app(environ, start_response):
        req = wo.Request(environ)
        resp = wo.Response(request=req, content_type="text/html; charset=UTF8")
        resp.body = 'hello world'
        return resp(environ, start_response)

    if __name__ == "__main__":
        wrs.make_server('', 8000, app).serve_forever()

To check this works, run ``myapp.py``, and use a web browser to open ``http://localhost:8000/``. You should see ``hello world``.

.. note:: The finished files at the end of this tutorial are in the tw2.forms source repository, in the examples directory.


Using Widgets
-------------

We'll now add some widgets to the application. Update the code to this::

    import webob as wo, wsgiref.simple_server as wrs, os
    import tw2.core as twc, tw2.forms as twf

    class TestPage(twc.Page):
        title = 'ToscaWidgets Tutorial'
        class child(twf.TableForm):
            name = twf.TextField()
            group = twf.SingleSelectField(options=['', 'Red', 'Green', 'Blue'])
            notes = twf.TextArea()

    def app(environ, start_response):
        req = wo.Request(environ)
        resp = wo.Response(request=req, content_type="text/html; charset=UTF8")
        resp.body = TestPage.display().encode('utf-8')
        return resp(environ, start_response)

    if __name__ == "__main__":
        wrs.make_server('', 8000, twc.TwMiddleware(app)).serve_forever()

When you look at this with a browser, it should be like this:

.. image:: tut1.png


Customising the Form
--------------------

You can change the form structure by editing the definition in the code. The widget browser shows all the widgets and options available in tw2.forms.

To customise the appearance of the form, we need to use a stylesheet. Create ``myapp.css`` with this content::

    h1 { color: red; }
    th { font-weight: normal; }
    tr.even { background-color: yellow; }
    .required th { font-weight: bold; }
    .error span { font-weight: bold; color: red; }

Edit ``myapp.py`` and add to the ``TestPage`` class::

    resources = [twc.CSSLink(filename='myapp.css')]

When you view the form, you should see this:

.. image:: tut2.png

To customise the layout of the page, we can use our own template for the ``Page`` widget. Create ``mypage.html`` with this content::

    <html>
        <head><title>$w.title</title></head>
        <body>
            <h1>$w.title</h1>
            This is some custom text
            ${w.child.display()}
        </body>
    </html>

Edit ``myapp.py`` and add to the ``TestPage`` class::

    template = 'genshi:%s/myapp.html' % os.getcwd()

The page should look this this:

.. image:: tut3.png

With these three techniques to use, you should be able to customise the form in almost any way you need. I encourage you to experiment with this for a while, before continuing with the tutorial. We will later cover validation, and creating your own widgets.

.. note:: The tutorial used a simple approach for referring to the CSS and template files. This would not usually be used in a real application. See the design document for more information.


Validation
----------

We can configure validation on form fields like this::

    class child(twf.TableForm):
        name = twf.TextField(validator=twc.Required)
        group = twf.SingleSelectField(options=['', 'Red', 'Green', 'Blue'])
        notes = twf.TextArea(validator=twc.StringLengthValidator(min=10))

To enable validation we also need to modify the application to handle POST requests::

    def app(environ, start_response):
        req = wo.Request(environ)
        resp = wo.Response(request=req, content_type="text/html; charset=UTF8")
        if req.method == 'GET':
            resp.body = MyForm.idisplay().encode('utf-8')
        elif req.method == 'POST':
            try:
                data = MyForm.validate(req.POST)
                resp.body = 'Posted successfully ' + wo.html_escape(repr(data))
            except twc.ValidationError, e:
                resp.body = e.widget.display().encode('utf-8')
        return resp(environ, start_response)

If you submit the form with some invalid fields, you should see this:

.. image:: tut4.png


Creating Widgets
----------------

 * Decide what base class to use
 * Identify parameters
 * Write template
 * Add any ``prepare()`` code you need
