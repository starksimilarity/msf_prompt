from __future__ import unicode_literals
import logging

from prompt_toolkit.history import FileHistory


import pymetasploit3.msfrpc as msfrpc
import pymetasploit3.msfconsole as msfconsole

from offpromptsession import OffPromptSession
from msf_prompt_styles import msf_style, get_prompt_text
from utils import parseargs

# future: add setuptools

HISTORY_FILENAME = ".off_prompt_hist"


def main():
    logging.basicConfig(
        filename=".off_prompt.log",
        format="===================\n%(asctime)s\n%(message)s",
        level=logging.INFO,
    )

    try:
        o = parseargs()  # future: replace with config file
        logging.info("Starting MsfRpcClient, MsfRpcConsole, OffPromptSession")
        client = msfrpc.MsfRpcClient(**o.__dict__)
        console = msfconsole.MsfRpcConsole(client)
        sess = OffPromptSession(
            console, hist_name=HISTORY_FILENAME, allow_overrides=True
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
