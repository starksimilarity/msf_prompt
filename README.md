# msf_prompt

msf_prompt is a Python library that emulates the msfconsole by wrapping a pymetasploit3 MsfRpcConsole in a prompt_toolkit PromptSession

pymetasploit3: (https://github.com/DanMcInerney/pymetasploit3)
prompt_toolkit: (https://github.com/prompt-toolkit/python-prompt-toolkit)

## Installation

Tested from a clean install of Ubuntu 18.04:
```bash
> sudo apt-get install python3
> sudo apt-get install python3-pip
> pip3 install setuptools
> sudo apt-get install git
> git clone https://github.com/starksimilarity/msf_prompt.git
> sudo python3 setup.py install
```

## Usage

Stand-alone
```bash
> python msf_prompt.py
```

As a module
```python
import offpromptsession 
import pymetasploit3


client = pymetasploit3.msfrpc.MsfRpcClient()
console = pymetasploit3.msfconsole.MsfRpcConsole(client)
sess = offpromptsession.OffPromptSession(console)

sess.prompt() #interact
```

To modify users/targets
```bash
> python usr_tgt_mod.py
```


## Module Interactions
![Module Interations](msf_prompt_flow.png)

## License
[GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
