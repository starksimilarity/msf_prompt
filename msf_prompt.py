from __future__ import unicode_literals
import logging

from prompt_toolkit.history import FileHistory


import pymetasploit3.msfrpc as msfrpc
import pymetasploit3.msfconsole as msfconsole

from offpromptsession import OffPromptSession
from msf_prompt_styles import msf_style, get_prompt_text
from utils import parseargs, parseconfig

# future: add setuptools

HISTORY_FILENAME = ".off_prompt_hist"
CONFIG_FILENAME = "prompt_config"
LOGGING_FILENAME = ".off_prompt_log"


def main():

    try:
        o = parseargs()  # returns a Values object
        opts = parseconfig(CONFIG_FILENAME)
        opts.update(o.__dict__)  # override config values with commandline

        print(opts)
        logging.basicConfig(
            filename=opts.get("log_file", LOGGING_FILENAME),
            format="===================\n%(asctime)s\n%(message)s",
            level=logging.INFO,
        )

        hist = opts.get("history_file", HISTORY_FILENAME)
        allow_overrides = opts.get("allow_overrides", True)

        logging.info("Starting MsfRpcClient, MsfRpcConsole, OffPromptSession")
        client = msfrpc.MsfRpcClient(**opts)
        console = msfconsole.MsfRpcConsole(client)

        sess = OffPromptSession(
            console, hist_name=hist, allow_overrides=allow_overrides
        )
    except Exception as e:
        print(f"something when very wrong, {e}")
        logging.warning(f"something went very wrong {e}")

    # main user input loop
    while True:
        try:
            # get_prompt_text and msf_style are imported
            user_input = sess.prompt(
                get_prompt_text(sess.msf_console.prompt), style=msf_style
            )
            sess.handle_input(user_input)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            pass


if __name__ == "__main__":
    main()
