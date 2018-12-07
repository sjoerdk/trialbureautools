#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=6.0', 'icaclswrap']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Sjoerd Kerkstra",
    author_email='sjoerd.kerkstra@radboudumc.nl',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6'
    ],
    description="Command line utilities for the radboudumc trial bureau",
    entry_points={
        'console_scripts': [
            'tbt=trialbureautools.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='trialbureautools',
    name='trialbureautools',
    packages=find_packages(include=['trialbureautools']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/sjoerdk/trialbureautools',
    version='0.1.3',
    zip_safe=False,
)
