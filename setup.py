#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
import loki

setup(name='loki',
      version=loki.__version__,
      description='I/O Communication Library',
      author='Álan Crístoffer',
      author_email='acristoffers@gmail.com',
      url='https://www.github.com/acristoffers/Loki',
      packages=['loki', 'loki/drivers'],
      license="MIT",
      install_requires=[
          'pySerial'
      ]
      )
