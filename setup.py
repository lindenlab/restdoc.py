#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup

setup(name='restdoc',
      version='0.0.2',
      author="Stephen Sugden",
      author_email="glurgle@gmail.com",
      packages=['restdoc'],
      dependency_links = [
          'http://github.com/dkjer/validictory/tarball/master#egg=validictory',
          ],
      test_suite="restdoc.tests",
      install_requires=['prettytable==0.6',
                'urllib3==1.3',
                'validictory',
               ],
      scripts=['scripts/rdc'],
      )
