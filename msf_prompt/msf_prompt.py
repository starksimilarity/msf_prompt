"""An example controlling script for an OffPromptSession.

Creates an MsfRpcClient and MsfRpcConsole based on config files
and user input and then creates the OffPromptSession.  Establishes
the primary loop for prompting the user.
"""

from __future__ import unicode_literals
import logging

from prompt_toolkit.history import FileHistory

import pymetasploit3.msfrpc as msfrpc
import pymetasploit3.msfconsole as msfconsole

from offpromptsession import OffPromptSession
from msf_prompt_styles import msf_style, get_formatted_prompt
from utils.utils import parseargs, parseconfig
from utils.patch_stdout_shim import patch_stdout


CONFIG_FILENAME = "configs/prompt_config"
HISTORY_FILENAME = ".off_prompt_hist"
LOGGING_FILENAME = ".off_prompt_log"


def main():
    """Main loop for msf_prompt an example controlling script for an OffPromptSession

    Basic Flow:
        - Get configs (passed on command line and in config file)
        - Setup connections to msfrpcd and ancillary tasks (e.g. logging)
        - Begin user input loop
    """
    try:
        opts = parseconfig(CONFIG_FILENAME)
        o = parseargs()  # returns a Values object
        for k, v in o.__dict__.items():
            if k and v:
                # only override config file value if command line param is not None
                opts[k] = v

        logging.basicConfig(
            filename=opts.get("log_file", LOGGING_FILENAME),
            format="===================\n%(asctime)s\n%(message)s",
            level=logging.INFO,
        )
        with patch_stdout():
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
            # Keeps new info (e.g scan results, new session notification)
            #                                   above the user input line
            # Redirects all output through the default logger
            with patch_stdout():
                user_input = sess.prompt(
                    get_formatted_prompt(sess.prompt_text), style=msf_style
                )
                sess.handle_input(user_input)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception as e:
            print(f"something when very wrong, {e}")
            logging.warning(f"something went very wrong {e}")
            break


if __name__ == "__main__":
    main()
