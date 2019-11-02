from optparse import OptionParser


def parseargs():
    """Parses arguments from the command line.
    """
    p = OptionParser()
    p.add_option("-P", dest="password", help="Password for msfrpcd")
    p.add_option("-S", dest="ssl", help="Use SSL to connect to msfrpcd")
    p.add_option("-U", dest="username", help="Username for msfrpcd")
    p.add_option("-a", dest="server", help="IP address of the msfrpcd server")
    p.add_option("-p", dest="port", help="Listening port for msfrpcd")
    o, a = p.parse_args()

    return o


def parseconfig(filename):
    """Opens a configuration file and returns a dictionary of parameters

    Format of the config file is "parameter:value #comment"
    Lines that begin with # are ignored
    Whitespace lines are ignored
    
    Parameters
    ----------
    filename : str
        Filename of the config file to open

    Returns
    -------
    options : dict
        Dictionary of options set by the config file
    """
    options = {}
    try:
        with open(filename, "r+") as infi:
            for line in infi:
                if "#" in line:
                    opt, comment, *_ = line.split("#")
                elif line:
                    opt = line
                if opt:
                    param, val = opt.split(":")
                    param = param.strip()
                    val = val.strip().strip(
                        "'\""
                    )  # strip whitespace and quotes from the param and value
                    # unsure if removing the quotes is going to cause a BUG...

                    try:
                        val = int(val)  # try to convert to int
                    except Exception as e:
                        pass

                    # try to set True/False
                    if val == "True":
                        val = True
                    elif val == "False":
                        val = False

                    options[param] = val
    except FileNotFoundError as e:
        print(e)
    return options
