import os.path
import shutil
import subprocess

from flask import Blueprint, request, session

from server.env import Env
from server.routing.decorators import authorized_route

home_bp = Blueprint("home", __name__)


@home_bp.route('/', methods=["GET"])
@authorized_route
def home():
    if "key" not in request.args:
        return "missing public key", 400
    key = request.args["key"]

    user = session.get("user")
    username = user["sub"]
    role = user["role"]

    def _exec(cmd):
        __proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                encoding="utf-8")
        return __proc.returncode == 0, __proc.stdout if __proc.returncode == 0 else __proc.stderr

    def _save_key():
        if not os.path.isfile(f"/home/{username}/.ssh/authorized_keys"):
            os.makedirs(f"/home/{username}/.ssh")
            with open(f"/home/{username}/.ssh/authorized_keys", "w+") as authorized_keys:
                authorized_keys.write(f"{key}")
        else:
            if key.strip() not in [k.strip() for k in
                                   open(f"/home/{username}/.ssh/authorized_keys", "r").read().split("\n")]:
                with open(f"/home/{username}/.ssh/authorized_keys", "a") as authorized_keys:
                    authorized_keys.write(key)

    def _set_dir_perms():
        return _exec(f"chown -R {username}:{'root' if role == 'admin' else 'student'} /home/{username} && "
                     f"chmod -R 700 /home/{username}")

    def _copy_exam():
        if not os.path.isdir(f"/home/{username}/{Env.get('EXAM_ID')}"):
            shutil.copytree(f"/etc/skel/{Env.get('EXAM_ID')}", f"/home/{username}/{Env.get('EXAM_ID')}")

    def _save_user(name):
        if not os.path.isfile(f"/app/users/{name}"):
            with open(f"/app/users/{name}", "w+"):
                pass

    user_exists, err = _exec(f"id -u {username}")

    # user does not exist, tho this might be because of restarts
    if not user_exists:
        # create either admin or restricted user
        user_created, err = _exec(
            f"useradd -m -p $(openssl passwd -1 \"{Env.get('API_KEY')}\") -s /bin/bash -K UID_MIN=2000 {username} && "
            f"usermod -aG sudo {username}") if role == "admin" \
            else _exec(f"useradd -m -g student -s /bin/bash -K UID_MIN=3000 {username}")
        if not user_created:
            return f"failed to create user {username} with message {err}", 500

        _save_user(username)

        # save the provided public key
        _save_key()

        # if student does not have exam dir copy it
        if role != "admin":
            _copy_exam()

        # set permissions for folders accordingly
        perms, err = _set_dir_perms()
        if not perms:
            return f"failed to set permissions on {username}: {err}", 500

        if role == "admin":
            return "added key to new admin account", 201
    else:
        # add key to authorized_keys file
        _save_key()

        # if admin that is it
        if role == "admin":
            return "added key to admin account", 201

        # copy skel
        _copy_exam()

        # set perms again
        # set permissions for folders accordingly
        perms, err = _set_dir_perms()
        if not perms:
            return f"failed to set permissions on {username}: {err}", 500

    return Env.get("EXAM_ID"), 200
