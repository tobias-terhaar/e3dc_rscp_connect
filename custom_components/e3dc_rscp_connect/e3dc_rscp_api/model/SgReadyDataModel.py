"""Data class to hold all data about a storage system."""

from dataclasses import dataclass, field


@dataclass
class SgReadyDataModel:
    state: int | None = None
