import asyncio
from types import MappingProxyType

import pytest

from aiomisc import Service, entrypoint
from aiomisc_dependency import freeze, consumer, inject, dependency


async def test_register_dependency():

    @dependency
    async def foo():
        return 'Foo'

    @dependency
    async def spam(foo):
        return foo * 3

    freeze()

    @consumer
    async def consume(spam):
        return spam

    await consume() == 'FooFooFoo'


@pytest.mark.parametrize(
    'dependencies_list,dependencies_map', [
        (('foo', 'bar'), None),
        (('foo',), {'bar': 'bar'}),
        (None, {'foo': 'foo', 'bar': 'bar'}),
        (None, MappingProxyType({'foo': 'foo', 'bar': 'bar'})),
    ]
)
async def test_inject_dependencies(dependencies_list, dependencies_map):

    @dependency
    async def foo():
        return 'Foo'

    @dependency
    async def bar():
        return 'Bar'

    class Target:
        ...

    target = Target()

    await inject(
        target,
        dependencies_list=dependencies_list,
        dependencies_map=dependencies_map,
    )

    assert target.foo == 'Foo'
    assert target.bar == 'Bar'


@pytest.mark.parametrize(
    'dependencies_list,dependencies_map', [
        ({'foo': 'bar'}, {'foo': 'bar'}),
        (['foo', 'bar'], ['foo', 'bar']),
    ]
)
async def test_inject_dependencies_bad(dependencies_list, dependencies_map):

    class Target:
        ...

    target = Target()

    with pytest.raises(ValueError):
        await inject(
            target,
            dependencies_list=dependencies_list,
            dependencies_map=dependencies_map,
        )


def test_dependency_injection():

    @dependency
    async def foo():
        yield 'Foo'

    @dependency
    async def bar():
        yield 'Bar'

    class TestService(Service):
        __dependencies__ = ('foo', 'bar')

        async def start(self):
            ...

    service = TestService()

    with entrypoint(service):
        assert service.foo == 'Foo'
        assert service.bar == 'Bar'


def test_missed_dependency_exception():

    class TestService(Service):
        __dependencies__ = ('spam',)

        async def start(self):
            ...

    with pytest.raises(RuntimeError):
        with entrypoint(TestService()):
            ...


def test_graceful_dependency_shutdown():

    @dependency
    async def spam():
        resource = ['spam'] * 3
        yield resource
        resource.clear()

    class TestService(Service):
        __dependencies__ = ('spam',)

        async def start(self):
            ...

    service = TestService()

    resource = None
    with entrypoint(service):
        resource = service.spam
        assert resource == ['spam'] * 3

    assert resource == []


def test_set_dependency_in_init():

    @dependency
    async def answer():
        yield 777

    class TestService(Service):
        __dependencies__ = ('answer',)

        async def start(self):
            ...

    service = TestService(answer=42)

    with entrypoint(service):
        assert service.answer == 42


def test_coroutine_function_dependency():

    @dependency
    async def foo():
        await asyncio.sleep(0.1)
        return 'Foo'

    @dependency
    async def bar():
        return 'Bar'

    class TestService(Service):
        __dependencies__ = ('foo', 'bar',)

        async def start(self):
            ...

    service = TestService()

    with entrypoint(service):
        assert service.foo == 'Foo'
        assert service.bar == 'Bar'


def test_dependencies_for_dependencies():

    @dependency
    async def foo():
        return 'Foo'

    @dependency
    async def spam(foo):
        return foo * 3

    class TestService(Service):
        __dependencies__ = ('spam',)

        async def start(self):
            ...

    service = TestService()

    with entrypoint(service):
        assert service.spam == 'FooFooFoo'


def test_loop_dependency():
    injected_loop = None

    @dependency
    def need_loop(loop):
        nonlocal injected_loop
        injected_loop = loop

    with entrypoint() as loop:
        assert loop == injected_loop


def test_defaults_no_dependency():
    class TestService(Service):
        __dependencies__ = ('spam',)

        spam: str = 'default'

        async def start(self):
            pass

    service = TestService()

    with entrypoint(service):
        assert service.spam == 'default'


@pytest.mark.parametrize('default,expected', [
    (None, 'inited'),
    ('default', 'inited'),
])
def test_defaults_with_init(default, expected):
    @dependency
    async def spam():
        return 'spam'

    async def start(self):
        pass

    attrs = {
        'start': start,
        '__dependencies__': ('spam',),
    }
    if default:
        attrs['spam'] = default

    cls = type('TestService', (Service,), attrs)

    service = cls(spam='inited')

    with entrypoint(service):
        assert service.spam == expected


@pytest.mark.parametrize('default,expected', [
    (None, 'spam'),
    ('default', 'spam'),
])
def test_defaults_without_init(default, expected):
    @dependency
    async def spam():
        return 'spam'

    async def start(self):
        pass

    attrs = {
        'start': start,
        '__dependencies__': ('spam',),
    }
    if default:
        attrs['spam'] = default

    cls = type('TestService', (Service,), attrs)

    service = cls()

    with entrypoint(service):
        assert service.spam == expected


def test_dependency_injection_reuse():

    @dependency
    async def foo(bar):
        yield bar

    @dependency
    async def bar():
        yield object()

    class TestService(Service):
        __dependencies__ = ('foo', 'bar')

        async def start(self):
            ...

    service = TestService()

    with entrypoint(service):
        assert service.foo is service.bar


@pytest.mark.parametrize(
    'dependencies,dependencies_map', [
        (['baz'], {'foo': 'bar'}),
        (None, {'foo': 'bar', 'baz': 'baz'}),
    ]
)
def test_dependency_inject_mapping(dependencies, dependencies_map):

    @dependency
    async def foo():
        yield 'foo'

    @dependency
    async def baz():
        yield 'baz'

    class TestService(Service):
        __dependencies__ = dependencies
        __dependencies_map__ = dependencies_map

        bar: str
        baz: str

        async def start(self):
            ...

    service = TestService()

    with entrypoint(service):
        assert not hasattr(service, 'foo')
        assert hasattr(service, 'bar')
        assert service.bar == 'foo'
        assert service.baz == 'baz'
