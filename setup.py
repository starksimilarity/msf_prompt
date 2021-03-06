#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path


def read(fname):
    return open(path.join(path.dirname(__file__), fname)).read()


setup(
    name="msf_prompt",
    author="starksimilarity",
    version="0.1a",
    author_email="starksimilarity@gmail.com",
    description="A Python library that emulates the Metasploit Framework msfconsole",
    license="GPL",
    packages=find_packages(),
    scripts=["msf_prompt/usr_tgt_mod.py"],
    install_requires=["pymetasploit3>=1.0", "prompt_toolkit>=2.0", "setuptools"],
    python_requires=">=3.6.0",
    # package_data = [""], # consider for the pickle files
    # data_files = [""], # consider for the pickle files
    url="https://github.com/starksimilarity/msf_prompt",
    download_url="https://github.com/starksimilarity/msf_prompt/archive/master.zip",
    long_description=read("README.md"),
)
