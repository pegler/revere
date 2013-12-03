#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# -*- mode: python -*-
# vi: set ft=python :


import os
from setuptools import setup


README_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README')
DESCRIPTION = 'simple monitoring and system with pluggable data sources and alerts'
if os.path.exists(README_PATH): LONG_DESCRIPTION = open(README_PATH).read()
else: LONG_DESCRIPTION = DESCRIPTION


setup(
    name='revere',
    version='0.0.1',
    install_requires=['Flask==0.10.1','Flask-SQLAlchemy==1.0','argparse','tornado>=3','APScheduler>=2','Flask-WTF','requests>=2'],
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Matt Pegler',
    author_email='matt@pegler.co',
    url='https://github.com/pegler/revere/',
    packages=['revere'],
    scripts=['bin/revereserver.py'],
)
