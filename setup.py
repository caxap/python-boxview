
import re
from codecs import open
from setuptools import setup, find_packages

version = ''
with open('boxview/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')


readme = ''
with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()


setup(
    name='python-boxview',
    version=version,
    description='Python client library for Box View API',
    long_description=readme,
    author='Maxim Kamenkov',
    author_email='mkamenkov@gmail.com',
    url='https://github.com/caxap/python-boxview',
    packages=find_packages(),
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=['requests', 'six'],
    license='MIT',
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ]
)
