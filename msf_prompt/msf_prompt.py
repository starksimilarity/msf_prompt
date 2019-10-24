from __future__ import unicode_literals
import logging

from prompt_toolkit.history import FileHistory


import pymetasploit3.msfrpc as msfrpc
import pymetasploit3.msfconsole as msfconsole

from offpromptsession import OffPromptSession
from msf_prompt_styles import msf_style, get_formatted_prompt
from utils import parseargs, parseconfig


CONFIG_FILENAME = "configs/prompt_config"
HISTORY_FILENAME = ".off_prompt_hist"
LOGGING_FILENAME = ".off_prompt_log"


def main():

    try:
        o = parseargs()  # returns a Values object
        opts = parseconfig(CONFIG_FILENAME)
        opts.update(o.__dict__)  # override config values with commandline

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
            # check to see if the user is in an interactive shell from a victim
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
