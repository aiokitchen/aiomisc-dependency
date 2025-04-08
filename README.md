# aiomisc-dependency

Dependency injection plugin for [aiomisc](https://github.com/aiokitchen/aiomisc) built with
[aiodine](https://github.com/bocadilloproject/aiodine) library and supports pytest fixture style dependency injection.

## Installation

Installing from PyPI:

```bash
pip3 install aiomisc aiomisc-dependency
```

## How to Use

### Register Dependency

To register a dependency, you can use the `aiomisc_dependency.dependency` decorator.

```python
from aiomisc_dependency import dependency

@dependency
async def pg_engine():
    pg_engine = await create_engine(dsn=pg_url)
    yield pg_engine
    pg_engine.close()
    await pg_engine.wait_closed()
```

As you can see, a dependency can be an async generator function. Code after `yield` will be executed on teardown 
to correctly close the dependency.

Coroutine functions, non-async functions, and generators are also supported.

### Use Dependency

To use a dependency, you need to add its name to the `__dependencies__` property for every service that depends on it.
Specified dependencies will be injected as the service's attributes on entrypoint startup. If you need to map the 
dependency with a different name, use `__dependencies_map__`.

```python
from contextlib import suppress
from types import MappingProxyType

import aiohttp
from aiomisc.service.aiohttp import AIOHTTPService

class HealthcheckService(AIOHTTPService):

    __dependencies__ = ('pg_engine',)

    async def create_application(self):
        app = aiohttp.web.Application()
        app.add_routes([aiohttp.web.get('/ping', self.healthcheck_handler)])
        return app

    async def healthcheck_handler(self, request):
        pg_status = False
        with suppress(Exception):
            async with self.pg_engine.acquire() as conn:
                await conn.execute('SELECT 1')
                pg_status = True

        return aiohttp.web.json_response(
            {'db': pg_status},
            status=(200 if pg_status else 500),
        )


class RESTService(AIOHTTPService):

    __dependencies__ = ('pg_engine',)

    ...

class AnotherRESTService(AIOHTTPService):

    __dependencies_map__ = MappingProxyType({'pg_engine': 'engine'})

    ...
```

If any required dependency is not found on entrypoint startup, a `RuntimeError` will be raised.

You can set a dependency manually by adding it to the keyword arguments on service creation. This can be 
convenient in tests.

```python
from unittest import Mock

def test_rest_service():
    pg_engine_mock = Mock()
    service = RESTService(pg_engine=pg_engine_mock)
    ...
```

### Dependencies for Dependencies

You can use dependencies as arguments for other dependencies. Arguments will be injected automatically.

```python
@dependency
async def pg_connection(pg_engine):
    async with pg_engine.acquire() as conn:
        yield conn
```

### `loop` Built-in Dependency

The built-in `loop` dependency can be used if your dependency requires an event loop instance.

```python
import aioredis

@dependency
async def redis_pool(loop):
    pool = aioredis.create_pool(redis_url, loop=loop)
    yield pool
    pool.close()
    await pool.wait_closed()
```

## License

MIT
