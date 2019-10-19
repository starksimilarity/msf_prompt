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
