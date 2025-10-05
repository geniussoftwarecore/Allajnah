from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

def init_cache(app):
    cache.init_app(app)
    return cache

def invalidate_cache_key(key):
    cache.delete(key)

def invalidate_cache_pattern(pattern):
    cache.clear()
