"""
msf_prompt
==========

Author: starksimilarity <starksimilarity@gmail.com>

Description: msf_prompt is a Python library that emulates the msfconsole by wrapping a pymetasploit3 MsfRpcConsole in a prompt_toolkit PromptSession. 

"""
from .utils import *
from .offpromptsession import *

__version__ = "0.1a"
VERSION = tuple(__version__.split("."))

__all__ = [
    # Utils.
    "parseargs",
    "parseconfig",
    # Offpromptsession.
    "MsfAutoSuggest",
    "OffPromptSession",
    "InvalidTargetError",
    "InvalidPermissionError",
    "UserOverride",
    "UserOverrideDenied",
]
