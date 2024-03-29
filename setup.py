from setuptools import setup, find_packages
import sys, os

version = '0.1.1'

setup(name='elixirext.localized',
      version=version,
      description="This allows you to localize the data contained in your Elixir entities.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Nicolas Laurance, Yannick Brehon',
      author_email='nicolas[dot]laurance<at>gmail[dot]com',
      url='http://code.google.com/p/elixirlocalized',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'elixir',
          'zope.interface',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
