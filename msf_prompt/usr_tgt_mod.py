from __future__ import unicode_literals
import ipaddress
import logging
import pickle
from collections import namedtuple

from prompt_toolkit import PromptSession

DEFAULT_USER_MODULE_FILE = "configs/user_module_list.pickle"
DEFAULT_ALLOWED_TARGETS_FILE = "configs/allowed_targets.pickle"

# future: add a bunch of comments

def print_targets(tgts):
    for t in tgts:
        print(f"[*] {str(t)}")


def get_targets(prompt):
    # future: make this not a pickle...
    targets = pickle.load(open(DEFAULT_ALLOWED_TARGETS_FILE, "rb"))
    print(f"The current target white-list is:")
    print_targets(targets)

def add_target(prompt):
    targets = pickle.load(open(DEFAULT_ALLOWED_TARGETS_FILE, "rb"))
    target = prompt.prompt("Enter a target or CIDR to add to white-list: ")
    try:
        targets.append(ipaddress.ip_address(target))
    except Exception as e:
        targets.append(ipaddress.ip_network(target))
    print(f"The new target white-list is:")
    print_targets(targets)
    pickle.dump(targets, open(DEFAULT_ALLOWED_TARGETS_FILE, "wb"))


def delete_target(prompt):
    targets = pickle.load(open(DEFAULT_ALLOWED_TARGETS_FILE, "rb"))
    target = prompt.prompt("Enter a target to delete from white-list: ")
    try:
        tgt = ipaddress.ip_address(target)
    except Exception as e:
        tgt = ipaddress.ip_network(target)
    if tgt in targets:
        targets[:] = [x for x in targets if x != tgt]
    elif target == "*":
        # future: prompt to double check before they blow away the whole target list
        targets = []
    else:
        print(f"[-] {target} was not found in the target white-list")
    print(f"The new target white-list is:")
    print_targets(targets)
    pickle.dump(targets, open(DEFAULT_ALLOWED_TARGETS_FILE, "wb"))


def get_permissions(prompt):
    # future: make this not a pickle...
    permissions = pickle.load(open(DEFAULT_USER_MODULE_FILE, "rb"))
    print(f"The current permission list is {permissions}")


def add_permission(prompt):
    permissions = pickle.load(open(DEFAULT_USER_MODULE_FILE, "rb"))
    perm = prompt.prompt("Enter a user:module permission to add: ")
    try:
        user, module = perm.split(":")
        permissions.get(user, []).append(module)
    except Exception as e:
        print(e)
    print(f"The new permission list is {permissions}")
    pickle.dump(permissions, open(DEFAULT_USER_MODULE_FILE, "wb"))


def delete_permission(prompt):
    permissions = pickle.load(open(DEFAULT_USER_MODULE_FILE, "rb"))
    perm = prompt.prompt("Enter a user:module permission to delete: ")
    try:
        user, module = perm.split(":")
        perms = permissions[user]
        if module == "*":
            permissions.pop(user)
        elif module not in perms:
            print(f"{module} not in {perms}")
        else:
            perms[:] = [x for x in perms if x != module]

    except Exception as e:
        print(e)
    print(f"The new permission list is {permissions}")
    pickle.dump(permissions, open(DEFAULT_USER_MODULE_FILE, "wb"))


Option = namedtuple("Option", ["prompt", "callback"])

# Be sure to define the callback above before adding to the list
prompt_options = {
    1: Option("List Targets", get_targets),
    2: Option("Add Target", add_target),
    3: Option("Delete Target", delete_target),
    4: Option("List Permissions", get_permissions),
    5: Option("Add Permission", add_permission),
    6: Option("Delete Permission", delete_permission),
}


def main():
    p = PromptSession()
    while True:
        print("\n")
        for k, v in prompt_options.items():
            print(f"{str(k)}. {v.prompt}")
        ret = p.prompt(f"\nSelect an option > ")
        try:
            ret = int(ret)
        except Exception as e:
            print("Please select a number from above")
            continue
        if ret not in prompt_options.keys():
            print("Please select a number from above")
            continue

        try:
            prompt_options[ret].callback(p)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
