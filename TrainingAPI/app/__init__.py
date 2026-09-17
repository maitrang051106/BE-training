from sanic import Sanic
from sanic_cors import CORS

from app.hooks.setup_ import disconnect_cache, setup_cache
from app.misc.log import log
from config import Config

import os
import bcrypt

from app.databases.mongodb import MongoDB


def register_extensions(sanic_app: Sanic):
    sanic_app.config.CORS_ORIGINS = "*"
    CORS(sanic_app)

    # OpenAPI swagger
    sanic_app.ext.openapi.add_security_scheme(
        'BearerAuth',
        'http',
        scheme='bearer',
        bearer_format='JWT',
    )
    sanic_app.ext.openapi.raw(Config.raw)

def register_routes(sanic_app: Sanic):
    from app.apis import api

    sanic_app.blueprint(api)

def register_hooks(sanic_app: Sanic):
    from app.hooks.request_context import after_request
    from app.hooks.error import _ApiError, api_error_handler

    sanic_app.register_middleware(after_request, 'response')
    sanic_app.exception(_ApiError)(api_error_handler)
    sanic_app.register_listener(setup_cache, event="before_server_start")
    sanic_app.register_listener(disconnect_cache, event="after_server_stop")



def create_app(*config_cls) -> Sanic:
    log(message='Sanic application initialized with {}'.format(', '.join([config.__name__ for config in config_cls])),
        keyword='INFO')

    sanic_app = Sanic(__name__)

    for config in config_cls:
        sanic_app.config.update_config(config)

    register_extensions(sanic_app)
    register_routes(sanic_app)
    register_hooks(sanic_app)

    return sanic_app

def create_admin():
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            "ADMIN_USERNAME and ADMIN_PASSWORD must be configured"
        )

    db = MongoDB()
    existing_user = db.get_user(username)

    if existing_user:
        if existing_user.get("role") != "admin":
            raise RuntimeError(
                f"User '{username}' exists but is not an admin"
            )
        return

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    if not db.add_user(username, password_hash, "admin"):
        raise RuntimeError("Could not create admin user")

    print(f"Admin user '{username}' created")