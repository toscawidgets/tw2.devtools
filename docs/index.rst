.. index:

tw2.devtools
============

To keep tw2.core as minimal as possible, features needed only for development are in a separate package, tw2.devtools. The features in devtools are:

 * Widget browser
 * Widget library quick start


Widget Browser
==============

The browser essentially enumerates the ``tw2.widgets`` entrypoint.

The parameters that are displayed are: all the required parameters, plus non-required parameters that are defined on anything other than the Widget base class. Variables are never shown.


Widget Library Quick Start
==========================

To create a widget library, issue::

    paster quickstart -t tw2.library tw2.mylib

This creates an empty template that gets you started.
