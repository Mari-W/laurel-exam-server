#!/usr/bin/env python3
"""
Author: Marius Weidner <weidner@cs.uni-freiburg.de>
REQUIRED PACKAGES: `ssh` `sshfs` `python3.x`
REQUIRED PYTHON3 LIBRARY: `requests`
"""
import json
import os.path
import subprocess
import sys
import urllib.parse
import requests

from dataclasses import dataclass, field
from getpass import getpass

# ---------------------------------------------------------------------------------------------------------------------

# CONSTS

# set static variables

# ---------------------------------------------------------------------------------------------------------------------

AUTH_URL = os.environ.get("AUTH_URL", "https://auth.laurel.informatik.uni-freiburg.de")
AUTH_COOKIE = os.environ.get("AUTH_COOKIE", "proglang-auth")
EXAM_URL = os.environ.get("EXAM_URL", "https://exam.laurel.informatik.uni-freiburg.de")
EXAM_SSH = os.environ.get("EXAM_SSH", "exam.laurel.informatik.uni-freiburg.de")


# ---------------------------------------------------------------------------------------------------------------------

# STORE

# file based dictionary for saving your authentication token

# ---------------------------------------------------------------------------------------------------------------------


@dataclass
class Store:
    __body: dict = field(default_factory=lambda: {})
    __file: str = ".cli.store.json"

    def __post_init__(self):
        if os.path.isfile(self.__file):
            with open(self.__file, "r", encoding="utf-8") as f:
                self.__body = json.load(f)
        else:
            with open(self.__file, "w", encoding="utf-8") as f:
                f.write("{}")
                self.__body = {}

    def __getitem__(self, item):
        # actually this is kinda ambiguous, as this returns None if key not found and
        # does not throw a ValueError, like a normal dict
        # tho, controversial option, this should be the default behaviour :angry:
        return self.__body.get(item)

    def __setitem__(self, key, value):
        self.__body[key] = value
        with open(self.__file, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.__body))


# ---------------------------------------------------------------------------------------------------------------------

# API

# logs into the system, can be used to interact with all services needed

# ---------------------------------------------------------------------------------------------------------------------

@dataclass
class Session:
    __session: requests.Session = field(default_factory=lambda: requests.Session())
    __username: str = None

    def __post_init__(self):
        if AUTH_COOKIE not in self.__session.cookies:
            self.__session.cookies.set(AUTH_COOKIE, store["AUTH_COOKIE"])

        r = self.__session.get(f"{AUTH_URL}/auth/me")

        if r.status_code != 200:
            print("Hi there!")
            print("Please login using your university account.")

            if AUTH_COOKIE in self.__session.cookies:
                self.__session.cookies.pop(AUTH_COOKIE)

            username = str(input("> Username: ")).strip()
            password = str(getpass("> Password: ")).strip()

            r = self.__session.post(f"{AUTH_URL}/auth/login?silent=true",
                                    json={"username": username, "password": password})

            if r.status_code != 200:
                if r.status_code == 401:
                    print("Invalid username or credentials.")
                    return self.__post_init__()
                else:
                    print("Login failed.")
                    print(f"API responded: {r.status_code}: {r.text}")
                    print("Please contact server administrator")
                    exit(1)
            else:
                store["AUTH_COOKIE"] = self.__session.cookies.get(AUTH_COOKIE)
                print("Login successful.")
                return self.__post_init__()
        else:
            self.__username = json.loads(r.text)["username"]

    @property
    def username(self):
        return self.__username

    def get(self, url):
        try:
            return self.__session.get(url)
        except requests.RequestException as e:
            print(f"{url} seems to be offline.")
            print(f"Server responded with: {e}")
            print("Please contact server administrator")
            exit(1)

    def post(self, url, json_data):
        try:
            return self.__session.post(url, json=json_data)
        except requests.RequestException as e:
            print(f"{url} seems to be offline.")
            print(f"Server responded with: {e}")
            print("Please contact server administrator")
            exit(1)


# ---------------------------------------------------------------------------------------------------------------------

# SSH

# ensures mounted directory

# ---------------------------------------------------------------------------------------------------------------------


@dataclass
class SSH:
    exam_id: str = None

    def __post_init__(self):
        res = session.get(f"{EXAM_URL}?key={urllib.parse.quote_plus(self.get_public_key())}")

        if res.status_code == 201:
            print(f"Added public key, you can now ssh to {EXAM_SSH} as admin")
            exit(0)

        if not res.status_code == 200:
            print(f"Failed to contact exam server at {EXAM_URL}")
            print(f"Server responded with: {res.text}")
            print("Please contact server administrator")
            exit(1)

        self.exam_id = res.text
        print(f"Joined {self.exam_id}.")
        self.mount_folder()
        print(f"Mounted corresponding server directory.")
        self.open_vs_code()
        print(f"Opened vscode in mounted directory.")
        print(f"Good luck! :)")
        exit(0)

    def mount_folder(self):
        sshfs_installed, err = self.exec("dpkg -l | grep sshfs")
        if not sshfs_installed:
            print("SSHFS ist not installed.")
            print("Please contact administrator.")
            print(f"Error: {err}")
            exit(1)

        if not os.path.isdir(os.path.expanduser(f"~/{self.exam_id}")):
            os.makedirs(os.path.expanduser(f"~/{self.exam_id}"))

        mounted, err = self.exec(
            f"sshfs -o IdentityFile={os.path.expanduser(f'~/.ssh/{session.username}.pub')} "
            f"{session.username}@{EXAM_SSH}:/home/{session.username}/{self.exam_id} "
            f"{os.path.expanduser(f'~/{self.exam_id}')}")
        if not mounted:
            if "mountpoint is not empty" in err:
                unmount, err = self.exec(f"fusermount -u {os.path.expanduser(f'~/{self.exam_id}')}")
                if not unmount:
                    print("Failed to unmount server directory.")
                    print("Please contact administrator.")
                    print(f"Error: {err}")
                    exit(1)
                return self.mount_folder()
            print("Failed to mount server directory.")
            print("Please contact administrator.")
            print(f"Error: {err}")
            exit(1)

    def open_vs_code(self):
        open_code, err = self.exec(f"code {os.path.expanduser(f'~/{self.exam_id}')}")
        if not open_code:
            print("Failed to open vs code.")
            print("Please contact administrator.")
            print(f"Error: {err}")
            exit(1)

    def get_public_key(self):
        if not os.path.isfile(os.path.expanduser(f"~/.ssh/{session.username}.pub")):
            if os.path.isfile(os.path.expanduser(f"~/.ssh/{session.username}")):
                os.remove(os.path.expanduser(f"~/.ssh/{session.username}"))
            key_created, out = self.exec(
                f"ssh-keygen -b 2048 -t rsa -f {os.path.expanduser(f'~/.ssh/{session.username}')} -N \"\"")
            if not key_created:
                print("Could not create public key.")
                print("Please contact administrator.")
                print(f"Error: {out}")
                exit(1)
            print("Generated new key pair.")
            return self.get_public_key()
        else:
            if not os.path.isfile(os.path.expanduser(f"~/.ssh/{session.username}")):
                os.remove(os.path.expanduser(f"~/.ssh/{session.username}.pub"))
                return self.get_public_key()
            else:
                with open(os.path.expanduser(f"~/.ssh/{session.username}.pub"), "r", encoding="utf-8") as key:
                    return key.read()
        # unreachable

    @staticmethod
    def exec(cmd):
        __proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                encoding="utf-8")
        return __proc.returncode == 0, __proc.stdout if __proc.returncode == 0 else __proc.stderr


if __name__ == '__main__':
    # order matters here as global objects get created, most of the time used by objects below them
    if "logout" in sys.argv:
        if os.path.isfile(".cli.store.json"):
            os.remove(".cli.store.json")

    # create cli store where authentication token is stored
    store = Store()

    # session which will ensure you are authorized after it's creation
    session = Session()  # uses: store

    # actual logic and communicating with courses server
    ssh = SSH()  # uses: session, git
