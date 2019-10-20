#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path


def read(fname):
    return open(path.join(path.dirname(__file__), fname)).read()


setup(
    name='msf_prompt',
    author='starksimilarity',
    version='0.1',
    author_email='starksimilarity@gmail.com',
    description='A Python library that emulates the Metasploit Framework msfconsole',
    license='GPL',
    packages=find_packages(exclude='tests'),
    scripts=[
        'usr_tgt_mod.py',
    ],
    install_requires=[
        'msgpack',
        'requests'
    ],
    url='https://github.com/starksimilarity/msf_prompt',
    download_url='https://github.com/starksimilarity/msf_prompt/archive/master.zip',
    long_description=read('README.md')
)

