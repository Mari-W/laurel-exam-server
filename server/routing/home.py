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

    if user["role"] == "admin":
        return f"admin user {username} cannot participate in exams", 500

    def _exec(cmd):
        __proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                encoding="utf-8")
        return __proc.returncode == 0, __proc.stdout if __proc.returncode == 0 else __proc.stderr

    # user does not exist, create it
    user_exists, _ = _exec(f"id -u {username}")
    if not user_exists:
        # create user
        user_created, err = _exec(f"useradd -m -g student -s /bin/bash -K UID_MIN=3000 {username}")
        if not user_created:
            return f"failed to create user {username}: {err}", 500

    # save the provided public key
    if not os.path.isfile(f"/home/{username}/.ssh/authorized_keys"):
        if not os.path.isdir(f"/home/{username}/.ssh"):
            os.makedirs(f"/home/{username}/.ssh")
        with open(f"/home/{username}/.ssh/authorized_keys", "w+") as authorized_keys:
            authorized_keys.write(f"{key}")
    else:
        if key.strip() not in [k.strip() for k in
                               open(f"/home/{username}/.ssh/authorized_keys", "r").read().split("\n")]:
            with open(f"/home/{username}/.ssh/authorized_keys", "a") as authorized_keys:
                authorized_keys.write(f"{key}\n")

    # copy exam if it is not present
    if not os.path.isdir(f"/home/{username}/{Env.get('EXAM_ID')}"):
        shutil.copytree(f"/etc/skel/{Env.get('EXAM_ID')}", f"/home/{username}/{Env.get('EXAM_ID')}")

    # set permissions for folders accordingly
    perms, err = _exec(f"chown -R {username}:student /home/{username} && "
                       f"chmod -R 700 /home/{username}")
    if not perms:
        return f"failed to set permissions on {username}: {err}", 500

    return Env.get("EXAM_ID"), 200


@home_bp.route('/exam', methods=["GET"])
@authorized_route
def exam():
    return Env.get("EXAM_ID"), 200
