#!/usr/bin/python3
import os
import re
import subprocess

import setuptools
from drag import VERSION

def extract_version():
    match = re.match(r'([-_.0-9a-z]+)(\+?)', VERSION)
    if match:
        if match[2] == '':
            return match[1]
        else:
            return match[1] + '.post'
    exit(f"Malformed VERSION {VERSION}")


def describe_or_extract_version():
    if 'FORCE_VERSION' in os.environ:
        return os.environ['FORCE_VERSION']
    ret = subprocess.run(['git', 'describe'], capture_output=True, text=True)
    if ret.returncode != 0:
        return extract_version()
    else:
        match = re.match('^v?([0-9]+.[0-9]+.[0-9]+)(-([0-9]+))?', ret.stdout)
        if match:
            if match[3] is None:
                return match[1]
            else:
                return match[1] + '.post' + match[3]
        else:
            return extract_version()


with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name="drag",
    version=describe_or_extract_version(),
    author="Marcel Waldvogel",
    author_email="marcel.waldvogel@trifence.ch",
    description="Webhook listener dragging along the main Docker process",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/MarcelWaldvogel/drag",
    license='AGPLv3',
    packages=setuptools.find_packages(),
    install_requires=['requests', 'setuptools'],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'drag=drag.server:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Natural Language :: English",
    ],
)
