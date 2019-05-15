import pytest

from aiomisc_dependency import reset_store


@pytest.fixture(autouse=True)
def reset_dependency_store():
    reset_store()
    yield
