#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name='pyyaml-include',
    packages=find_packages('src'),
    package_dir={'': 'src'},

    description='Extending PyYAML with a custom constructor for including YAML files within YAML files',
    url='https://github.com/tanbro/pyyaml-include',
    license='GNU General Public License v3 or later (GPLv3+)',
    author='liu xue yan',
    author_email='liu_xue_yan@foxmail.com',
    keywords='yaml PyYAML include',

    use_scm_version={
        # guess-next-dev: automatically guesses the next development version (default)
        # post-release:   generates post release versions (adds postN)
        'version_scheme': 'guess-next-dev',
        'write_to': 'src/yamlinclude/version.py',
    },

    python_requires='>=3.5',

    setup_requires=['setuptools_scm', 'setuptools_scm_git_archive'],
    install_requires=['PyYAML>=5.3.1,<6.0'],
    extras_require={
        'all': ['toml'],
        'toml': ['toml'],
    },
    tests_require=['toml'],

    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup',
    ],
)
