"""Setuptools setup file"""

import sys, os

from setuptools import setup

def get_description(fname='README.txt'):
    # Adapted from PEAK-Rules' setup.py
    # Get our long description from the documentation
    f = file(fname)
    lines = []
    for line in f:
        if not line.strip():
            break     # skip to first blank line
    for line in f:
        if line.startswith('Documentation contents'):
            break     # read to "Documentation contents..."
        lines.append(line)
    f.close()
    return ''.join(lines)


# Requirements to install buffet plugins and engines
_extra_cheetah = ["Cheetah>=1.0", "TurboCheetah>=0.9.5"]
_extra_genshi = ["Genshi >= 0.3.5"]
_extra_kid = ["kid>=0.9.5", "TurboKid>=0.9.9"]
_extra_mako = ["Mako >= 0.1.1"]

# Requierements to run all tests
_extra_tests = _extra_cheetah + _extra_genshi + _extra_kid + _extra_mako + ['BeautifulSoup', 'WebTest']


setup(
    name='tw2.devtools',
    version='2.0.0-alpha1',
    description="Web widget creation toolkit based on TurboGears widgets - development tools",
    long_description = get_description(),
    install_requires=[
        'tw2.core',
        'paste',
        'pastescript',
        'weberror',
        ],
    extras_require = {
        'cheetah': _extra_cheetah,
        'kid': _extra_kid,
        'genshi': _extra_genshi,
        'mako': _extra_mako,
        'build_docs': [
            "Sphinx",
            ],
        },
    tests_require = _extra_tests,
    url = "http://toscawidgets.org/",
    download_url = "http://toscawidgets.org/download/",
    author='Paul Johnston, Alberto Valverde & contributors',
    author_email='paj@pajhome.org.uk',
    license='MIT',
    test_suite = 'tests',
    packages = ['tw2.devtools'],
    namespace_packages = ['tw2'],
    include_package_data=True,
    exclude_package_data={"thirdparty" : ["*"]},
    entry_points="""
    [paste.paster_create_template]
    tw2.library=tw2.paste_template:ToscaWidgetsTemplate

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


"""
    [distutils.commands]
    archive_tw_resources = tw.core.command:archive_tw_resources
"""
