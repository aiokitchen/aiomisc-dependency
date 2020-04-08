import logging
from collections import namedtuple
from functools import wraps
from typing import Mapping, Sequence, AbstractSet

from aiodine.store import Store


log = logging.getLogger(__name__)

STORE = Store()

NOT_FOUND_DEP = object()


def dependency(func):
    return STORE.provider(scope='session')(func)


def _aggregate(*, dependencies_list, dependencies_map) -> dict:
    dependencies = {name: name for name in dependencies_list}

    overlapping = set(dependencies.keys()) & set(dependencies_map.keys())
    if overlapping:
        log.warning(
            '__dependencies__ and __dependencies_map__ overlap with %s',
            overlapping
        )

    dependencies.update(dependencies_map)
    return dependencies


async def inject(target, *, dependencies_list, dependencies_map):
    dependencies_list = dependencies_list or []
    dependencies_map = dependencies_map or {}
    if (
        not isinstance(dependencies_list, (AbstractSet, Sequence)) or
        not isinstance(dependencies_map, Mapping)
    ):
        raise ValueError(
            '__dependencies__ must be a sequence or a set, '
            'whereas __dependencies_map__ must be a mapping'
        )

    dependencies = _aggregate(
        dependencies_list=dependencies_list,
        dependencies_map=dependencies_map,
    )

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
