# msf_prompt

msf_prompt is a Python library that emulates the msfconsole by wrapping a pymetasploit3 client in a prompt_toolkit PromptSession

## Installation

## Usage

Stand-alone
```bash
> python msf_prompt.py
```

As a module
```python
import msf_prompt
import pymetasploit3

sess = msf_prompt.OffPromptSession(pymetasploit3.msfrpc.MsfRpcClient())
```
