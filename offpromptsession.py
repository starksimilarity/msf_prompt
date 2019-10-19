from __future__ import unicode_literals
import string
import logging
import re
import os
import pickle

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.shortcuts import yes_no_dialog

import pymetasploit3.msfrpc as msfrpc
import pymetasploit3.msfconsole as msfconsole

from msf_prompt_styles import msf_style, get_prompt_text

# future: add setuptools

# The file that stores user permissions for modules
USER_MODULE_FILE = "user_module_list.pickle"
# The file that stores list of valid targets
ALLOWED_TARGETS_FILE = "allowed_targets.pickle"


class InvalidTargetError(Exception):
    pass


class InvalidPermissionError(Exception):
    pass


class UserOverride(Exception):
    pass


class UserOverrideDenied(Exception):
    pass


class msfValidator(Validator):
    """
    Implements Validator ABC.  Ensures input into the msf_prompt passes certain checks
    (e.g. valid target, user has permission for tool, etc)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, document):
        """this seems to get called on every keystroke; would rather have something
        that gets called on submitting input; investigate more"""
        print(document)
        return


class OffPromptSession(PromptSession):
    """Main class that wraps pymetasploit3 MsfRpcConsole with prompt_toolkit.PromptSession

    Attributes
    ----------
    auto_suggest : prompt_toolkit.auto_suggest.AutoSuggestFromHistory
        auto populate line based on user's history
    completer : prompt_toolkit.completion.WordCompleter
        suggests completion to user based on string currently typed
    msf_console : pymetasploit3.msfconsole.MsfRpcConsole
        console session for MetasploitFramework
    wordlist : list
        list of words to populate the completer

    Methods
    -------
    handle_input(self, text)
        Main callback for when the user submits input
    validate_targets(self, targets)
        Ensure targets are on approved white list
    validate_user_perms(self, module)
        Ensure user has permission to run module.
    allowed_modules(self, user)
        Returns list of allowed modules for a given user.
    """

    wordlist = []
    with open("word_suggestions.txt", "r+") as infi:
        wordlist = infi.read().strip().split(",")
        print(wordlist)

    def __init__(self, console, hist_name=None, allow_overrides=False, *args, **kwargs):
        """
        Parameters
        ----------
        console : pymetasploit3.msfconsole.MsfRpcConsole
            console session for MetasploitFramework
        hist_name : str, optional
            string name to the command history file
        allow_overrides : Bool, optional
            flag to determine if user can override warnings for target and module errors
        *args, **kwargs:
            args to override default PromptSession behavoir
        """

        self.msf_console = console
        self._allow_overrides = allow_overrides
        # self.history=None
        # try:
        #    self.history = FileHistory(hist_name)
        # except Exception as e:
        #    logging.info('probably no hist_name passed; in-memory history only')
        _history = FileHistory(hist_name)
        super().__init__(history=_history, *args, **kwargs)
        self.completer = WordCompleter(self.wordlist, ignore_case=True)
        self.enable_history_search = True
        self.auto_suggest = AutoSuggestFromHistory()
        # self.validator = msfValidator()

    def handle_input(self, text):
        """
        Main callback for when the user submits input
    
        Parameters
        ----------
        text : str
            The user-submitted command
        
        Returns
        -------
        None
        
        Raises
        ------
        Exception
            General Error
        UserOverride
            If user elects to override warning
        UserOverrideDenied
            If user declines to override warning
        """

        try:
            lower_text = (
                text.lower().strip()
            )  # temp variable to prevent re-writing text.lower().strip() all the time

            if (
                lower_text == "exit"
            ):  # BUG: probably some bad side effects here (i.e. exitting session instead of shell)
                exit(0)

            if lower_text.startswith("exploit"):
                """getting the attributes of the module is going to be difficult;
                instead the program will check against valid list when user enters; investigate more"""
                # validate targets
                # validate user permissions

                # prompt for confirm if 'exploit'
                confirm = yes_no_dialog(
                    title="Confirm Exploit", text="Confirm Submission"
                )
                if confirm:
                    pass
                else:
                    raise Exception("User aborted exploitation")

            ############################################
            # Validate rhost against allowed target file
            ############################################
            elif lower_text.startswith("set") and "rhost" in lower_text:

                # find all IPs in 'set' command
                # future: add hostnames as well
                targets = re.findall("(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", text)
                try:
                    self.validate_targets(targets)

                except InvalidTargetError as e:
                    print(e)
                    logging.warning(f"<<< {str(e)}")

                    if self.allow_overrides:
                        # ask user if they want to override the warning
                        override = yes_no_dialog(
                            title="Target Override",
                            text="An invalid target was added; do you want to continue anyway?",
                        )
                        if override:
                            raise UserOverride(
                                "{self.current_user} overrode warning {e}"
                            )
                        else:
                            raise UserOverrideDenied(
                                "{self.current_user} chose not to overide warning {e}"
                            )
                    else:
                        raise UserOverrideDenied(
                            "{self.current_user} attempted disallowed action: {e}"
                        )

            #######################################################################
            # Validate selected module against list of allowed modules for the user
            #######################################################################
            elif lower_text.startswith("use"):
                try:
                    module = re.findall("use (.*)", lower_text)[0]
                    self.validate_user_perms(module)
                except InvalidPermissionError as e:
                    print(e)
                    logging.warning(f"<<< {str(e)}")

                    if self.allow_overrides:
                        # ask user if they want to override the warning
                        override = yes_no_dialog(
                            title="User Module Permission Override",
                            text="The current user does not have permission to run the selected module. \
                                    Would you like to continue anyway?",
                        )
                        if override:
                            raise UserOverride(
                                "{self.current_user} overrode warning {e}"
                            )
                        else:
                            raise UserOverrideDenied(
                                "{self.current_user} chose not to overide warning {e}"
                            )
                    else:
                        raise UserOverrideDenied(
                            "{self.current_user} attempted disallowed action: {e}"
                        )

                except Exception as e:
                    print(e)
                    logging.warning(f"<<< {str(e)}")

            ######################
            # finally do something
            ######################
            self.msf_console.execute(text)

        except UserOverride as e:
            # user approved warning override
            # future consider sending this to alternate/remote logs
            logging.warning(f"USER WARNING OVERRIDE: {e}")
            # execute command
            self.msf_console.execute(text)

        except UserOverrideDenied as e:
            # user chose not to override warning message
            logging.warning(f"WARNING OVERRIDE DENIED: {e}")
            # do not execute command

        except Exception as e:
            print(str(e))
            logging.warning(f"<<< {str(e)}")

    def validate_targets(self, targets):
        """
        Ensure targets are on approved white list

        Parameters
        ----------
            targets : list[str]
                List of strings representing string of RHOST IPs

        Returns
        -------
            Exception or True

        Raises
        ------
            InvalidTargetError
                Raised on first occurnace of invalid target within list of targets
        """

        for target in targets:
            if target not in self.allowed_targets:
                raise InvalidTargetError(f"Warning {target} is not on allowed list")
        return True

    def validate_user_perms(self, module):
        """
        Ensure user has permission to run module.

        Parameters
        ----------
            module : str
                String name of the requested module; does not include prefix (e.g. "exploit")

        Returns
        -------
            True if user has permission otherwise raises exception

        Raises
        ------
            InvalidPermissionError
                If user does not have permission to run selected module
        """

        # future: get user allowed modules from db
        # future: allow wildcards in allowed list
        user_allowed_modules = self.allowed_modules(self.current_user)

        if module not in user_allowed_modules:
            raise InvalidPermissionError(
                f"Warning user does not have permission to run {module}"
            )
        return True

    @property
    def current_user(self):
        return os.getlogin()

    @property
    def allow_overrides(self):
        return self._allow_overrides

    def allowed_modules(self, user):
        """
        Returns list of allowed modules for a given user.
        
        Parameters
        ----------
            user : str
                String name of the user.

        Returns
        -------
            module_list.get(user, [])
                List of approved modules for a given user, otherwise empty list for unknown user
        """

        # future: make this a DB not a pickle
        module_list = []
        with open(USER_MODULE_FILE, "rb") as infi:
            module_list = pickle.load(infi)
        return module_list.get(user, [])

    @property
    def allowed_targets(self):
        tgts = []
        try:
            with open(ALLOWED_TARGETS_FILE, "rb") as infi:
                tgts = pickle.load(infi)
        except Exception as e:
            print(e)
            logging.warning(f"<<< {str(e)}")

        return tgts
