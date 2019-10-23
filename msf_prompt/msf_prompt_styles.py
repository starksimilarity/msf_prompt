from prompt_toolkit.styles import Style
import re
import string

msf_style = Style.from_dict(
    {
        # user input
        "": "white",
        # Prompt
        "msf": "white underline",
        "module": "ansired bold",
        "plain": "white",
    }
)


def get_formatted_prompt(raw_text):
    """
    Get formatted prompt from msfrpc prompt

    Parameters
    ----------
        raw_text : str
            Raw prompt returned from pymetasploit3 msfclient rpc prompt

    Returns
    -------
        prompt_text : list
            List of tuples descibing prompt formatting

    """

    try:
        msf = re.findall("msf[0-9]?", raw_text)[0]
    except:
        # probably in an interactive shell
        return [('', raw_text)]
    try:
        premodule = re.findall("( [\w]+)\(", raw_text)[0]
    except:
        premodule = ""
    try:
        module = re.findall("\((.*?)\)", raw_text)[0]
        module = "".join([x for x in module if string.printable.__contains__(x)])
    except:
        module = ""
    if len(module) > 0:
        openparen = "("
        closeparen = ")"
    else:
        openparen = ""
        closeparen = ""

    prompt_text = [
        ("class:msf", msf),
        ("class:plain", premodule),
        ("class:plain", openparen),
        ("class:module", module),
        ("class:plain", closeparen),
        ("class:plain", " > "),
    ]

    return prompt_text
