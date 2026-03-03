#!/usr/bin/env python

"""
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
"""

from setuptools import setup

setup(name='bely_api',
      version='2025.3.dev1',
      packages=["belyApi",
                "belyApi.api",
                "belyApi.models"],
      py_modules=["BelyApiFactory"],
      install_requires=['python-dateutil', 
          'urllib3',
          'certifi',
          'six'],
      license='Copyright (c) UChicago Argonne, LLC. All rights reserved.',
      description='Python client API library used to communicate with BELY API.',
      maintainer='Dariusz Jarosz',
      maintainer_email='djarosz@aps.anl.gov',
      url='https://git.aps.anl.gov/controls/hla/bely',
      entry_points={
        'console_scripts': [
          'bely-test = BelyApiFactory:run_command'
        ]
      })
