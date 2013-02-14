#!/usr/bin/env python

from setuptools import setup

setup(name='potluck',
      version='1.0',
      description='Potluck website',
      author='Jonathan Villemaire-Krajden',
      author_email='odontomachus@gmail.com',
      install_requires = [
        'bottle',
        'MySQL-python',
        'twisted',
        ]
     )
