from sanic import Sanic

from app.databases.redis_cached import RedisCache
from app.misc.log import log


async def setup_cache(sanic_app: Sanic):
    cache = RedisCache()
    await cache.connect()
    sanic_app.ctx.cache = cache

    log('Setup cache connections')


async def disconnect_cache(sanic_app: Sanic):
    cache = getattr(sanic_app.ctx, 'cache', None)
    if cache:
        await cache.disconnect()