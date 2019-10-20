from optparse import OptionParser


def parseargs():
    p = OptionParser()
    p.add_option("-P", dest="password", help="Password for msfrpcd", default="password")
    p.add_option(
        "-S", dest="ssl", help="Use SSL to connect to msfrpcd", default=True
    )  # BUG: make this true/false
    p.add_option("-U", dest="username", help="Username for msfrpcd", default="msf")
    p.add_option(
        "-a",
        dest="server",
        help="IP address of the msfrpcd server",
        default="127.0.0.1",
    )
    p.add_option("-p", dest="port", help="Listening port for msfrpcd", default=55553)
    o, a = p.parse_args()

    return o


def parseconfig(filename):
    """Opens a configuration file as returns a dictionary of parameters

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
    with open(filename, "r+") as infi:
        for line in infi:
            if "#" in line:
                opt, comment, *_ = line.split("#")
                if len(opt) > 0:
                    param, val = opt.split(":")
                    param = param.strip()
                    val = val.strip().strip(
                        "'\""
                    )  # strip whitespace and quotes from the param and value
                    # unsure if removing the quotes is going to cause a BUG...

                    try:
                        val = int(val)
                    except Exception as e:
                        pass

                    if val == "True":
                        val = True
                    elif val == "False":
                        val = False

                    options[param] = val
    return options
