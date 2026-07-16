from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class DiscoveryResult:
    discovery_id: str
    payload: Mapping[str, object]


class StructureDiscovery(Protocol):
    @property
    def discovery_id(self) -> str:
        ...

    def discover(self, context: Mapping[str, object]) -> DiscoveryResult:
        ...


class DiscoveryRegistry:
    def __init__(self) -> None:
        self._discoveries: dict[str, StructureDiscovery] = {}

    def register(self, discovery: StructureDiscovery) -> None:
        discovery_id = discovery.discovery_id
        if discovery_id in self._discoveries:
            raise ValueError(f"duplicate discovery_id: {discovery_id}")
        self._discoveries[discovery_id] = discovery

    def get(self, discovery_id: str) -> StructureDiscovery:
        try:
            return self._discoveries[discovery_id]
        except KeyError as exc:
            raise KeyError(f"unknown discovery_id: {discovery_id}") from exc

    def list_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._discoveries))
