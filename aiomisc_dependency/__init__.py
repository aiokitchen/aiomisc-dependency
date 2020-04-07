from collections import namedtuple
from functools import wraps
from typing import Mapping

from aiodine.store import Store


STORE = Store()

NOT_FOUND_DEP = object()


def dependency(func):
    return STORE.provider(scope='session')(func)


def _construct_mapping(dependencies) -> dict:
    if isinstance(dependencies, Mapping):
        return dict(dependencies)

    return dict([
        (dep, dep) if isinstance(dep, str) else dep
        for dep in dependencies
    ])


async def inject(target, dependencies):
    dependencies = _construct_mapping(dependencies)

    deps_holder = namedtuple('DepsHolder', list(dependencies.keys()))

    @wraps(deps_holder)
    async def async_deps_holder(*args):
        return deps_holder(*args)

    resolved_deps = await STORE.consumer(async_deps_holder)(
        *([NOT_FOUND_DEP] * len(dependencies))
    )

    for name in dependencies:
        value = getattr(resolved_deps, name)
        target_name = dependencies[name]

        # Check that has default class value non-overriden by init.
        default = (
             hasattr(target, target_name) and
             hasattr(target.__class__, target_name) and
             getattr(target, target_name) == getattr(
                target.__class__, target_name
             )
        )

        if not hasattr(target, target_name) or default:
            if value is NOT_FOUND_DEP:
                # If default class value => no injection
                if not default:
                    raise RuntimeError(
                        "Required %s dependency wasn't found", name
                    )
                else:
                    continue

            setattr(target, target_name, value)


async def enter_session():
    return await STORE.enter_session()


async def exit_session():
    return await STORE.exit_session()


def freeze():
    return STORE.freeze()


def consumer(*args, **kwargs):
    return STORE.consumer(*args, **kwargs)


def reset_store():
    global STORE
    STORE = Store()


__all__ = (
    'dependency', 'enter_session', 'exit_session', 'freeze', 'consumer',
    'inject', 'reset_store',
)
