# msf_prompt

msf_prompt is a Python library that emulates the msfconsole by wrapping a pymetasploit3 client in a prompt_toolkit PromptSession

## Installation

## Usage

```bash
python msf_prompt.py
```

```python
import msf_prompt
sess = msf_prompt.OffPromptSession(pymetasploit3.msfrpc.MsfRpcClient())
```
