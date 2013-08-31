#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup

setup(name='restdoc',
      version='0.0.2',
      author="Stephen Sugden",
      author_email="glurgle@gmail.com",
      packages=['restdoc'],
      test_suite="restdoc.tests",
      requires=['prettytable (==0.6)',
                'urllib3 (==1.3)',
                'validictory (>=0.9.2)',
               ],
      scripts=['scripts/rdc'],
      )
