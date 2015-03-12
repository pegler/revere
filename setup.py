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
    install_requires=[
        # 'Flask==0.10.1',
        # 'Flask-SQLAlchemy==1.0',
        # 'argparse','tornado>=3',
        # 'APScheduler==2.1.2',
        # 'Flask-WTF',
        # 'requests>=2',
        'APScheduler==2.1.2',
        'Flask==0.10.1',
        'Flask-GoogleAuth==0.4',
        'Flask-SQLAlchemy==1.0',
        'Flask-WTF==0.9.4',
        'Jinja2==2.7.2',
        'MarkupSafe==0.18',
        'SQLAlchemy==0.9.1',
        'SQLAlchemy-Utils==0.23.3',
        'WTForms==1.0.5',
        'WTForms-Alchemy==0.12.0',
        'WTForms-Components==0.9.1',
        'Werkzeug==0.9.4',
        'backports.ssl-match-hostname==3.4.0.2',
        'blinker==1.3',
        'decorator==3.4.0',
        'infinity==1.3',
        'intervals==0.2.0',
        'itsdangerous==0.23',
        'requests==2.2.1',
        'six==1.5.2',
        'toolz==0.5.2',
        'tornado==3.2',
        'validators==0.5.0',
        'wsgiref==0.1.2',
    ],
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Matt Pegler',
    author_email='matt@pegler.co',
    url='https://github.com/pegler/revere/',
    packages=['revere'],
    scripts=['bin/revereserver.py'],
)
