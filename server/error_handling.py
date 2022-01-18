import traceback

from authlib.integrations.base_client import MismatchingStateError, OAuthError
from flask import session
from telegram import Bot
from werkzeug.exceptions import NotFound
from werkzeug.utils import redirect

from server.env import Env

if Env.get_bool("TELEGRAM_LOGGING", required=False):
    bot = Bot(Env.get("TELEGRAM_TOKEN"))


def error_handling(app):
    @app.errorhandler(MismatchingStateError)
    def state_error(_):
        return redirect("/auth/logout")

    @app.errorhandler(NotFound)
    def not_found(_):
        return "route does not exist", 404

    @app.errorhandler(OAuthError)
    def oauth_error(_):
        return redirect("/auth/login")

    if Env.get_bool("TELEGRAM_LOGGING", required=False):
        @app.errorhandler(Exception)
        def all_exception_handler(error):
            send_error(error)


def send_error(exception: Exception):
    text = f"""ERROR occurred on BUILD SERVER

Logged in user: {session.get("user")}

Error: {type(exception).__name__}
Message: {exception}

Stacktrace:
{''.join(traceback.format_tb(exception.__traceback__))}
"""
    print(text)
    if Env.get_bool("TELEGRAM_LOGGING", required=False):
        bot.sendMessage(chat_id=Env.get("TELEGRAM_CHAT_ID"), text=text)
