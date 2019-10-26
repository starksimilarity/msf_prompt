"""
utils
=====

Author: starksimilarity <starksimilarity@gmail.com>

Description: utility modules for msf_prompt.  Provides argument and config parsing and 
output redirection with logging.
"""

from .utils import *
from .patch_stdout_shim import *

__all__ = [
    # Utils.
    "parseargs",
    "parseconfig",
    # patch_stdout_shim
    "patch_stdout",
    "LoggingStdoutProxy",
]
