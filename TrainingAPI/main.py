import os

from sanic.response import text

from app import create_app, create_admin
from app.apis import api
from app.misc.log import log
from config import Config, LocalDBConfig

app = create_app(Config, LocalDBConfig)

@app.route("/", methods={'GET'})
async def hello_world(request):
    return text("Hello World")


if __name__ == '__main__':
    create_admin()
    if 'SECRET_KEY' not in os.environ:
        log(message='SECRET KEY is not set in the environment variable.', keyword='WARN')
    app.run(**app.config['RUN_SETTING'])
