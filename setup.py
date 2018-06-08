#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='pyyaml-include',
    packages=find_packages('src'),
    package_dir={'': 'src'},

    description='Extending PyYAML with a custom constructor for including YAML files within YAML files',
    url='https://github.com/tanbro/pyyaml-include',
    author='liu xue yan',
    author_email='liu_xue_yan@foxmail.com',

    use_scm_version={
        # guess-next-dev:	automatically guesses the next development version (default)
        # post-release:	generates post release versions (adds postN)
        'version_scheme': 'guess-next-dev',
    },
    setup_requires=['setuptools_scm', 'setuptools_scm_git_archive'],

    install_requires=[
        'PyYAML',
    ],

    test_suite='tests.test_all',

    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*'
)
