from . import freeze, enter_session, exit_session, inject, dependency


async def resolve_dependencies(entrypoint, services):

    @dependency
    def loop():
        return entrypoint.loop

    freeze()
    await enter_session()
    for svc in services:
        dependencies_list = getattr(svc, '__dependencies__', None)
        dependencies_map = getattr(svc, '__dependencies_map__', None)
        if dependencies_list or dependencies_map:
            await inject(
                svc,
                dependencies_list=dependencies_list,
                dependencies_map=dependencies_map,
            )


async def clear_dependencies(entrypoint):
    await exit_session()


def setup():
    from aiomisc import entrypoint

    entrypoint.PRE_START.connect(resolve_dependencies)
    entrypoint.POST_STOP.connect(clear_dependencies)
