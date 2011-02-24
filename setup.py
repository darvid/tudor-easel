#!/usr/bin/env python2
"""
    easel
    ~~~~~

    Manage, manipulate, and export 16-color VGA palettes to templates.

    :copyright: Copyright 2011 David Gidwani.
    :license: BSD style, see LICENSE
"""
from setuptools import setup, find_packages
from easel import __version__


setup(
    name="tudor-easel",
    version=__version__,
    license="BSD",
    description=__doc__,
    packages=["easel"],
    namespace_packages=["easel"],
    include_package_data = True,
    install_requires=["PyGTK >= 2.12", "commons >= 0.0.1"]
    entry_points={
        "console_scripts": ["easel = easel.application:main"]
    }
)
