import os
import subprocess
from datetime import timedelta

from flask import Flask

from server.error_handling import error_handling
from server.env import Env
from server.oauth import init_oauth
from server.routing.auth import auth_bp
from server.routing.cli import cli_bp
from server.routing.home import home_bp


def create_app():
    # init server
    app = Flask(__name__, template_folder="../templates")
    app.config.update(os.environ)

    # some dynamic settings
    app.config["SECRET_KEY"] = Env.get("API_KEY")
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=100)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # add routers
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cli_bp, url_prefix='/cli')

    # setup error handling
    error_handling(app)

    # init oauth client
    init_oauth(app)

    return app
