"""Setuptools setup file"""

import sys, os

from setuptools import setup, find_packages


setup(
    name='tw2.devtools',
    version='2.0b9',
    description="Web widget creation toolkit based on TurboGears widgets - development tools",
    long_description = open('README.txt').read().split('\n\n', 1)[1],
    install_requires=[
        'tw2.core>=2.0b4',
        'paste',
        'pastescript',
        'weberror',
        'docutils',
        "tw2.jquery",
        "tw2.jqplugins.ui",
        "tw2.protovis.custom",
        "pygments",
        "github2",
        "decorator",
        "genshi",
        "mako",
        ],
    extras_require = {
        'build_docs': [
            "Sphinx",
            ],
        },
    tests_require = [
        'WebTest',
        'BeautifulSoup',
        'nose',
        # Note -- formencode should not (and 'is' not) required here.
        # However, tw2.core needs it but doesn't declare it in pypi.  Therefore,
        # we include it here the make tests pass.  TODO -- this should be
        # removed.
        "formencode",
    ],
    url = "http://toscawidgets.org/documentation/tw2.core/",
    author='Paul Johnston, Christopher Perkins, Alberto Valverde & contributors',
    author_email='paj@pajhome.org.uk',
    license='MIT',
    test_suite = 'nose.collector',
    packages=find_packages(exclude=['ez_setup', 'tests']),
    namespace_packages = ['tw2'],
    include_package_data=True,
    exclude_package_data={"thirdparty" : ["*"]},
    entry_points="""
    [paste.paster_create_template]
    tw2.library=tw2.devtools.paste_template:ToscaWidgetsTemplate

    [paste.global_paster_command]
    tw2.browser=tw2.devtools.browser:WbCommand
    """,
    zip_safe=False,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Environment :: Web Environment :: ToscaWidgets',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Software Development :: Widget Sets',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
