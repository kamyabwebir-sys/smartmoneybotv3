import pytest

from smart_money.discovery.registry import (
    DiscoveryRegistry,
    DiscoveryResult,
)


class FakeDiscovery:
    def __init__(self, discovery_id: str) -> None:
        self._discovery_id = discovery_id
        self.discover_called = False

    @property
    def discovery_id(self) -> str:
        return self._discovery_id

    def discover(self, context):
        self.discover_called = True
        return DiscoveryResult(
            discovery_id=self.discovery_id,
            payload={"context": context},
        )


def test_register_and_get_discovery():
    registry = DiscoveryRegistry()
    discovery = FakeDiscovery("structure.alpha")

    registry.register(discovery)

    assert registry.get("structure.alpha") is discovery
    assert discovery.discover_called is False


def test_list_ids_is_deterministic():
    registry = DiscoveryRegistry()
    registry.register(FakeDiscovery("structure.beta"))
    registry.register(FakeDiscovery("structure.alpha"))
    registry.register(FakeDiscovery("structure.gamma"))

    assert registry.list_ids() == (
        "structure.alpha",
        "structure.beta",
        "structure.gamma",
    )


def test_duplicate_discovery_id_is_rejected():
    registry = DiscoveryRegistry()
    registry.register(FakeDiscovery("structure.alpha"))

    with pytest.raises(ValueError, match="duplicate discovery_id: structure.alpha"):
        registry.register(FakeDiscovery("structure.alpha"))


def test_unknown_discovery_id_is_rejected():
    registry = DiscoveryRegistry()

    with pytest.raises(KeyError, match="unknown discovery_id: structure.missing"):
        registry.get("structure.missing")


def test_discovery_result_is_immutable():
    result = DiscoveryResult(
        discovery_id="structure.alpha",
        payload={"score": 1},
    )

    with pytest.raises(AttributeError):
        result.discovery_id = "structure.beta"
