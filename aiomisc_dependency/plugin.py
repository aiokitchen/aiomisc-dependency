from .import freeze, enter_session, exit_session, inject, dependency


async def resolve_dependencies(entrypoint, services):

    @dependency
    def loop():
        return entrypoint.loop

    freeze()
    await enter_session()
    for svc in services:
        if hasattr(svc, '__dependencies__'):
            await inject(svc, svc.__dependencies__)


async def clear_dependencies(entrypoint):
    await exit_session()


def setup():
    from aiomisc import entrypoint

    entrypoint.PRE_START.connect(resolve_dependencies)
    entrypoint.POST_STOP.connect(clear_dependencies)
