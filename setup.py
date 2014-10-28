import os

from setuptools import setup, find_packages
from boxview import __version__


setup(
    name = 'python-boxview',
    version=__version__,
    description = 'Python client library for Box View API',
    author = 'Maxim Kamenkov',
    author_email = 'mkamenkov@gmail.com',
    url = 'https://github.com/caxap/python-boxview',
    packages = find_packages(),
    install_requires=[
        'requests==2.0.1',
        'six',
    ],
    license = 'MIT',
    zip_safe=False,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ]
)
