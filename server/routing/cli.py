from flask import Blueprint, render_template, Response

from server.env import Env
from server.routing.decorators import authorized_route

cli_bp = Blueprint("cli", __name__)


@cli_bp.route("/version")
@authorized_route
def version():
    return Env.get("CLI_VERSION"), 200


@cli_bp.route("/download")
def download():
    cli = render_template("cli", version=Env.get("CLI_VERSION"),
                          auth_url=Env.get("AUTH_URL"), auth_cookie=Env.get("AUTH_COOKIE"),
                          exam_url=Env.get("PUBLIC_URL"), exam_ssh=Env.get("PUBLIC_SSH"),
                          exam_ssh_port=Env.get("PUBLIC_SSH_PORT"),
                          read_only=Env.get_bool("READ_ONLY"))
    r = Response(response=cli, status=200, mimetype="text/python")
    r.headers["Content-Type"] = "text/python; charset=utf-8"
    return r
