"""
Moe
===
Moe is the most mysterious project in the Universe.

The project name derives from the word "moe" and it means "nice to import".
For example::

  from moe import awesomeness

See? It is nice.
"""
from setuptools import setup

setup(
    name = 'moe',
    version = '0.0',
    license = 'Apache Software License',
    url = 'http://www.tipfy.org/',
    description = 'Moe is the most mysterious project in the Universe.',
    long_description=__doc__,
    author = 'Rodrigo Moraes',
    author_email = 'rodrigo.moraes@gmail.com',
    zip_safe = False,
    platforms='any',
    packages = [
    ],
    include_package_data=True,
    install_requires = [
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
