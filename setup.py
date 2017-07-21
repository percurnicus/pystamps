#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='pystamps',
    version='0.1.0',
    description="View and select PDS images to open in pdsview or pdsspect",
    long_description=readme + '\n\n' + history,
    author="PlanetaryPy Developers",
    author_email='contact@planetarypy.com',
    url='https://github.com/planetarypy/pystamps',
    packages=[
        'pystamps',
    ],
    package_dir={'pystamps':
                 'pystamps'},
    include_package_data=True,
    install_requires=[
        'planetaryimage>=0.5.0',
        'matplotlib>=1.5.1',
        'QtPy>=1.2.1',
    ],
    license="BSD",
    zip_safe=False,
    keywords='pystamps',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    entry_points={
        'console_scripts': [
            'pystamps=pystamps.pystamps:cli'
        ],
    }
)
