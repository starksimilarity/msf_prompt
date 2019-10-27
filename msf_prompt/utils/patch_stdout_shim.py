"""
patch_stdout_shim
=================

Extends the prompt_toolkit patch_stdout module by creating the LoggingStdoutProxy and 
changing the patch_stdout function to create a LoggingStdoutProxy.  

There was no way to call into the original prompt_toolkit patch_stdout so the code is copied 
here so that it can create a LoggingStdoutProxy.  

Credit: Jonathan Slenders (jonathan@slenders.be)
https://github.com/prompt-toolkit/python-prompt-toolkit
"""
from __future__ import unicode_literals

from prompt_toolkit import patch_stdout as pso

from contextlib import contextmanager
import threading
import sys
import logging


class LoggingStdoutProxy(pso.StdoutProxy):
    """Extends prompt_toolkit StdoutProxy by adding logging to the write method

    All other attributes and methods are inherited from StdoutProxy 
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def write(self, data):
        with self._lock:
            self._write(data)
            if len(data.strip()) > 0:
                logging.info(f"[RESULT]\n{data}")


@contextmanager
def patch_stdout(raw=False):
    """
    Replace `sys.stdout` by an :class:`_StdoutProxy` instance.

    Writing to this proxy will make sure that the text appears above the
    prompt, and that it doesn't destroy the output from the renderer.  If no
    application is curring, the behaviour should be identical to writing to
    `sys.stdout` directly.

    :param raw: (`bool`) When True, vt100 terminal escape sequences are not
                removed/escaped.
    """
    proxy = LoggingStdoutProxy(raw=raw)

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    # Enter.
    sys.stdout = proxy
    sys.stderr = proxy

    try:
        yield
    finally:
        # Exit.
        proxy.flush()

        sys.stdout = original_stdout
        sys.stderr = original_stderr
