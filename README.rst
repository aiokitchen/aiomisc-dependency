aiomisc-dependency
==================

Dependency injection plugin for aiomisc_ built with aiodine_ library and
support pytest fixture style dependency injection.

.. _aiodine: https://github.com/bocadilloproject/aiodine
.. _aiomisc: https://github.com/aiokitchen/aiomisc

.. contents:: Table of contents


Installation
------------

Installing from pypi:

.. code-block:: bash

    pip3 install aiomisc aiomisc-dependency


How to use
----------

Register dependency
*******************

To register dependency you can use ``aiomisc_dependency.dependency`` decorator.

.. code-block:: python

    from aiomisc_dependency import dependency

    @dependency
    async def pg_engine():
        pg_engine = await create_engine(dsn=pg_url)
        yield pg_engine
        pg_engine.close()
        await pg_engine.wait_closed()


As you can see dependency can be async generator function. Code after yield
will be executed on teardown to correctly close the dependency.

Coroutine functions, non async functions and generators are also supported.


Use dependency
**************

To use dependency you need to add it's name to ``__dependencies__`` property
for every service which depends on it. Specified dependencies will be injected
as service's attributes on entrypoint startup.

.. code-block:: python

    from contextlib import suppress

    import aiohttp
    from aiomisc import Service
    from aiomisc.service.aiohttp import AIOHTTPService

    class HealthcheckService(Service):

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

If any required dependency won't be found on entrypoint startup,
``RuntimeError`` will be raised.

You can set a dependency manually by adding it to kw arguments on service
creation. This could be convenient in tests.

.. code-block:: python

    from unittest import Mock

    def test_rest_service():
        pg_engine_mock = Mock()
        service = RESTService(pg_engine=pg_engine_mock)
        ...

Dependencies for dependencies
*****************************

You can use dependencies as arguments for other dependencies. Arguments will
injected automatically.

.. code-block:: python

    @dependency
    async def pg_connection(pg_engine):
        async with pg_engine.acquire() as conn:
            yield conn


``loop`` built-in dependency
****************************

Built-in ``loop`` dependency can be used if your dependency requires
event loop instance.

.. code-block:: python

    import aioredis

    @dependency
    async def redis_pool(loop):
        pool = aioredis.create_pool(redis_url, loop=loop)
        yield pool
        pool.close()
        await pool.wait_closed()

LICENSE
-------

MIT
