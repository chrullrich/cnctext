#!/usr/bin/env python

from setuptools import setup


setup(
    name="CNCtext",
    version="0.1",
    description="Convert text to CNC G-code",
    author="Christian Ullrich",
    author_email="chris@chrullrich.net",
    license="CC0",  # why not?
    url="https://bitbucket.org/chrullrich/cnctext",
    packages=[
        "cnctext",
    ],
    package_data={
        "cnctext": [
            "fonts\*.chr",
        ],
    },
    entry_points={
        "console_scripts": [
            "cnctext = cnctext.app:console_entry_point",
        ],
    },
    install_requires=[
        "numpy",
        "arpeggio",
    ],
)