"""Setuptools setup file"""

import os

from setuptools import setup, find_packages

try:
    import multiprocessing
    import logging
except:
    pass

setup(
    name='tw2.devtools',
    version='2.2.0.2',
    description='The development tools for ToscaWidgets 2, a web widget toolkit.',
    long_description=open('README.txt').read().split('\n\n', 1)[1],
    author='Paul Johnston, Christopher Perkins, Alberto Valverde Gonzalez & contributors',
    author_email='toscawidgets-discuss@googlegroups.com',
    url="http://toscawidgets.org/",
    download_url="https://pypi.python.org/pypi/tw2.devtools/",
    license='MIT',
    install_requires=[
        'tw2.core>=2.1.0a',
        'gearbox',
        'weberror',
        'webhelpers',
        'docutils',
        "tw2.jquery",
        "tw2.jqplugins.ui",
        "pygments",
        "decorator",
        "genshi",
        "mako",
        ],
    extras_require={
        'build_docs': [
            "Sphinx",
            ],
        },
    tests_require=[
        'WebTest',
        'nose',
        'sieve',
    ],
    test_suite='nose.collector',
    packages=find_packages(exclude=['ez_setup', 'tests']),
    namespace_packages=['tw2'],
    include_package_data=True,
    exclude_package_data={"thirdparty": ["*"]},
    entry_points="""
    [paste.paster_create_template]
    tw2.library=tw2.devtools.paste_template:ToscaWidgetsTemplate

    [gearbox.commands]
    tw2.browser=tw2.devtools.browser:WbCommand

    [paste.server_runner]
    tw2_dev_server=tw2.devtools.server:dev_server

    """,
    zip_safe=False,
    classifiers=[
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
