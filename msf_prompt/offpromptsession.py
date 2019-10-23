from __future__ import unicode_literals
import string
import logging
import re
import os
import pickle

from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.completion import (
    WordCompleter,
    Completer,
    Completion,
    merge_completers,
)
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import *
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.shortcuts import yes_no_dialog

# The file that stores user permissions for modules
DEFAULT_USER_MODULE_FILE = "configs/user_module_list.pickle"
# The file that stores list of valid targets
DEFAULT_ALLOWED_TARGETS_FILE = "configs/allowed_targets.pickle"
# The file that contains a list of standard msfconsole commands
DEFAULT_COMPLETER_WORDLIST = "configs/word_suggestions.txt"
# The file that contains the list of user command history
DEFAULT_COMPLETER_WORDLIST = ".off_prompt_hist"


class InvalidTargetError(Exception):
    pass


class InvalidPermissionError(Exception):
    pass


class UserOverride(Exception):
    pass


class UserOverrideDenied(Exception):
    pass


class ShellExitError(Exception):
    """Raised when a user is in a shell and then exits back to the main console
    """
    pass


class MsfCompleter(Completer):
    """Class used for suggesting tab-complete strings to user

    MsfCompleter implements the CompleterABC and returns tab-completions based
    on what the msfrpc console returns from the 'tabs' method. The completer strips away
    anything after the next '/' so that the user isn't inundated with thousands of
    suggestions and instead just what the next word should be.

    Attributes
    ----------
    console : pymetasploit3.MsfRpcConsole
        current console that can be used to search through tab-complete

    Methods
    -------
    get_completions(self, document, compete_event)
        Main callback from when the user hits <tab>
    """

    def __init__(self, console):
        self.console = console

    def get_completions(self, document, complete_event):
        """Main callback from when a complete_event occurs (usually when the user hits <tab>)

        Parameters
        ----------
        buffer : prompt_toolkit.buffer.Buffer
        complete_event : prompt_toolkit.completion.CompleteEvent

        Yields
        ------
        _ : prompt_toolkit.completion.Completion
            single suggestion to the user wrapped by a Completion class
        """

        # main call to the rpc hook to get what msfrpcd thinks is a propper tab-complete
        full_completions = self.console.console.tabs(document.text)

        already_suggested = (
            []
        )  # keeps track of things already suggested to the user between yields
        for a in full_completions:
            partial_completion = a[len(document.text) :].split("/")[
                0
            ]  # from the cursor to the next '/'
            first_half = re.split("[ /]", a[: len(document.text)])[
                -1
            ]  # from the beginning of word to cursor
            comp = first_half + partial_completion
            if comp in already_suggested:
                # prevents duplicates from being suggested to the user
                # "already_suggested gets cleared on each time a CompleteEvent is called
                continue
            else:
                already_suggested.append(comp)
                # yield the entire text and input the text at the beginning of where the word begins
                yield Completion(comp, -len(first_half))


class MsfAutoSuggest(AutoSuggestFromHistory):
    """Class used for suggesting auto_complete strings to the user

    MsfAutoSuggest extends AutoSuggestFromHistory by adding a search through a static
    wordlist and then from the MsfRpcConsole's tab-complete functionality (console.console.tabs(str)). 
    The search order is: History, Static Wordlist, Console Tab-complete.

    Attributes
    ----------
    console : pymetasploit3.MsfRpcConsole
        current console that can be used to search through tab-complete
    wordlist : list[str]
        static list of words that are common for msfconsole

    Methods
    -------
    get_suggestion(self, buffer, document)
        Main callback for when an auto_suggest is called; usually when the buffer updates
    """

    def __init__(self, console, wordlist=None, **kwargs):
        """
        Parameters
        ----------
        console : pymetasploit3.MsfRpcConsole
            current console that can be used to search through tab-complete
        wordlist : list[str], optional
            static list of words that are common for msfconsole
        """

        self.console = console
        if wordlist:
            self.wordlist = wordlist
        else:
            self.wordlist = []

    def get_suggestion(self, buffer, document):
        """main callback when a suggestion is needed from auto_suggest

        The search order is : History, Static Wordlist, Console Tab-complete 
        
        Parameters
        ----------
        buffer : prompt_toolkit.buffer.Buffer
        document : prompt_toolkit.document.Document

        """

        # check user history first
        suggestion = super().get_suggestion(buffer, document)
        if suggestion is None:  # nothing in our history
            text = document.text.rsplit("\n", 1)[
                -1
            ]  # not totally sure what this does; stealing from AutoSuggestFromHistory
            if text.strip():  # don't suggest on a blank line
                # check the wordlist
                for word in self.wordlist:
                    if word.startswith(text):
                        suggestion = Suggestion(word[len(text) :])
                        break
                if suggestion is None:  # nothing from wordlist
                    # check tab complete suggestions from rpc
                    tabs = self.console.console.tabs(
                        text
                    )  # should return a list of strings that match tab-complete for the console
                    if tabs:
                        suggestion = Suggestion(
                            tabs[0][len(text) :]
                        )  # take the first one and suggest the rest of the word
        return suggestion

    # future
    # def get_suggestion_async


class MsfValidator(Validator):
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
    active_shell : OffPromptShellSession
        the shell the user has chosen to interact with
    auto_suggest : prompt_toolkit.auto_suggest.AutoSuggestFromHistory
        auto populate line based on user's history
    completer : prompt_toolkit.completion.WordCompleter
        suggests completion to user based on string currently typed
    module_filename : str
        filename of the file that maps users to allowed modules
    msf_console : pymetasploit3.msfconsole.MsfRpcConsole
        console session for MetasploitFramework
    prompt_text : str
        string that represents what should be displayed to user at the prompt
    target_filename : str
        filename of the file that defines allowed targets
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

    # future: make this an instance variable?
    wordlist = []
    with open(DEFAULT_COMPLETER_WORDLIST, "r+") as infi:
        wordlist = infi.read().strip().split(",")

    def __init__(
        self,
        console,
        hist_name=None,
        allow_overrides=False,
        module_filename=None,
        target_filename=None,
        *args,
        **kwargs,
    ):
        """
        Parameters
        ----------
        console : pymetasploit3.msfconsole.MsfRpcConsole
            console session for MetasploitFramework
        hist_name : str, optional
            string name to the command history file
        allow_overrides : Bool, optional
            flag to determine if user can override warnings for target and module errors
        module_filename 
            filename of the file that maps users to allowed modules
        target_filename : str, optional
            filename of the file that defines allowed targets
            
        *args, **kwargs:
            args to override default PromptSession behavoir
        """

        self.msf_console = console
        self._allow_overrides = allow_overrides
        self.active_shell = None

        if module_filename:
            self._module_filename = module_filename
        else:
            self._module_filename = DEFAULT_USER_MODULE_FILE
        if target_filename:
            self._target_filename = target_filename
        else:
            self._target_filename = DEFAULT_ALLOWED_TARGETS_FILE
        if hist_name:
            self.hist_name = hist_name
        else:
            self.hist_name = DEFAULT_HISTORY_FILENAME

        _history = FileHistory(self.hist_name)

        super().__init__(history=_history, *args, **kwargs)

        self.completer = MsfCompleter(self.msf_console)
        self.enable_history_search = True
        self.auto_suggest = MsfAutoSuggest(self.msf_console, self.wordlist)

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

            if self.active_shell:
                #send all input down to shell's handle_input function
                try:
                    self.active_shell.handle_input(text)
                except ShellExitError as e:
                    # Shell has exited
                    # BUG: is there a memory leak here....?
                    self.active_shell = None
            else:

                if (
                    lower_text == "exit"
                ):  # BUG: probably some bad side effects here (i.e. exitting session instead of shell)
                    exit(0)

                # handle when user wants to interact with a session
                elif lower_text.startswith("sessions -i"):
                    # In most cases, the goal is to offload most of the execution logic to msfrpcd,
                    # but in this case extra logic is needed to handle the creation of a new shell

                    # find which session the user wants to interact with
                    try:
                        requested_session = re.findall(
                            "sessions? -i\W+([0-9]{1,9})", lower_text
                        )[0]
                        if (
                            requested_session
                            in self.msf_console.console.rpc.sessions.list.keys()
                        ):
                            # Create new MsfSession (either MeterpreterSession or ShellSession)
                            # found valid session, now do something
                            shell = self.msf_console.console.rpc.sessions.session(
                                requested_session
                            )
                            # create a new object for them to interact with
                            shellSession = OffPromptShellSession(
                                shell, self.msf_console, hist_name=self.hist_name
                            )
                            self.active_shell = shellSession
                            # somehow gracefully get back to msfconsole when they exit?
                        else:
                            print(
                                f"[-] Invalid session identifier: {requested_session}"
                            )
                    except Exception as e:
                        print(e)
                        logging.warning(f"<<< {str(e)}")

                    # for now, raise an execption so execution doesn't occur
                    raise Exception(
                        "Interacting with sessions is not currently supported"
                    )

                elif lower_text.startswith("exploit"):
                    """getting the attributes of the module is going to be difficult;
                    instead the program will check against valid list when user enters; investigate more

                    turns out you can run console.execute("get [parameter (e.g. rhost)]") and you'll get
                    the answer back in as: "[parameter] => [value]"; need to look into this more
                    """
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
                                    f"{self.current_user} overrode warning: {e}"
                                )
                            else:
                                raise UserOverrideDenied(
                                    f"{self.current_user} chose not to overide warning: {e}"
                                )
                        else:
                            raise UserOverrideDenied(
                                f"{self.current_user} attempted disallowed action: {e}"
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
                                    f"{self.current_user} overrode warning: {e}"
                                )
                            else:
                                raise UserOverrideDenied(
                                    f"{self.current_user} chose not to overide warning: {e}"
                                )
                        else:
                            raise UserOverrideDenied(
                                f"{self.current_user} attempted disallowed action: {e}"
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
        user_allowed_modules = self.allowed_modules(self.current_user)

        if module not in user_allowed_modules:  # simple exact check
            for allowed_module in user_allowed_modules:
                # loop through modules that have a wildcard and see if the requested module starts with that
                # shortcut the loop and return True if found; otherwise the loop will end and raise an error
                # future: there's probably a more elegant/performant way to do this
                if "*" in allowed_module:
                    if module.startswith(allowed_module.strip("*")):
                        return True
            raise InvalidPermissionError(
                f"Warning {self.current_user} does not have permission to run {module}"
            )
        return True

    @property
    def current_user(self):
        return os.getlogin()

    @property
    def allow_overrides(self):
        return self._allow_overrides

    @property
    def target_filename(self):
        return self._target_filename

    @property
    def module_filename(self):
        return self._module_filename

    def allowed_modules(self, user):
        """
        Returns list of allowed modules for a given user.
        
        Parameters
        ----------
            user : str
                String name of the user.

        Returns
        -------
            module_list.get(user, []) + module_list.get('ALL', [])
                List of approved modules for a given user and all users, otherwise empty list
        """

        # future: make this a DB not a pickle
        module_list = []
        with open(self.module_filename, "rb") as infi:
            module_list = pickle.load(infi)

        return module_list.get(user, []) + module_list.get("ALL", [])

    @property
    def allowed_targets(self):
        """Loads and returns list of approved targets from ALLOWED_TARGET_FILE
        """
        tgts = []
        try:
            with open(self.target_filename, "rb") as infi:
                tgts = pickle.load(infi)
        except Exception as e:
            print(e)
            logging.warning(f"<<< {str(e)}")
        return tgts

    @property
    def prompt_text(self):
        """rpc call through the MsfRpcConsole to get the current prompt
        """
        if self.active_shell:
            return self.active_shell.prompt_text
        else:
            return self.msf_console.prompt


class OffPromptShellSession(OffPromptSession):
    """Extension of OffPromptSession used for shells from targets

    Launched when a user types "interact -i [#]" at the OffPromptSession console.
    An OffPromptShellSession is much less featured than its parent and disables
    the completer and auto_suggest since there's not a non-trivial way to do that with 
    a generic shell.

    Attributes
    ----------
    parent_console : OffPromptSession
        unclear if this is a link to or a deep copy of the parent console
    shell : pymetasploit3.msfrpc.ShellSession
        The shell instance the user is interacting with
    """

    def __init__(self, shell, console, *args, **kwargs):
        """The OffPromptSession comes with a lot of functionality that standard shells
        won't have so this init will turn a lot of them off.

        # future : consider a refactor where there is a more basic superclass and the 
        subclasses implement more, not the other way around
        """
        super().__init__(console, *args, **kwargs)
        # Turn off the normal OffPromptSession features
        self.completer = None
        self.enable_history_search = False
        self.auto_suggest = None

        # There's currently no non-trivial way of getting the shell's prompt
        self._prompt_text = "unknown-shell > "
        self.parent_console = console
        self.shell = shell

    @property
    def prompt_text(self):
        return self._prompt_text

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
        ShellExitError 
            Raised when the user wants to exit the shell and return to main msfconsole
        """
        try:
            lower_text = (
                text.lower().strip()
            )  # temp variable to prevent re-writing text.lower().strip() all the time

            # Breakout of shell and set parent console to no active shell
            # BUG: This probably has bad side-effects as currently implemented (e.g. nested shells)
            if lower_text == "background" or lower_text == "exit":
                raise ShellExitError(lower_text)

            elif lower_text:
                print(self.shell.run_with_output(text, "DummyString", timeout=10))
        except ShellExitError as e:
            # pass up to the next level to set the active_shell to None
            raise e
        except Exception as e:
            print(e)
            logging.warning(f"<<< {str(e)}")
