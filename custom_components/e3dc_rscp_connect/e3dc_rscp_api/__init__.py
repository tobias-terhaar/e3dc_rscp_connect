"""Communication layer for E3/DC storage systems.

This package talks RSCP to the device: it opens the connection, builds the
request frames, and extracts the answers into plain data models. It is
self-contained and free of Home Assistant imports, so it can be released as a
standalone library later on.

Everything a consumer needs is re-exported here — importing from the modules
below is an implementation detail of this package:

    from .e3dc_rscp_api import RscpClient, StorageDataModel

The data models are plain dataclasses; they are the only thing a consumer
should read. Nothing outside this package needs to know about RSCP tags,
frames or encryption.
"""

from .client import RscpClient
from .exceptions import (
    E3dcAuthenticationError,
    E3dcConnectionError,
    E3dcIdentificationError,
    E3dcRscpError,
)
from .model.SgReadyDataModel import SgReadyDataModel
from .model.StorageDataModel import (
    DeviceState,
    DeviceStates,
    EmsPowerModel,
    PvInverterData,
    StorageDataModel,
)
from .model.WallboxDataModel import WallboxCurrentModel, WallboxDataModel

__all__ = [
    "DeviceState",
    "DeviceStates",
    "E3dcAuthenticationError",
    "E3dcConnectionError",
    "E3dcIdentificationError",
    "E3dcRscpError",
    "EmsPowerModel",
    "PvInverterData",
    "RscpClient",
    "SgReadyDataModel",
    "StorageDataModel",
    "WallboxCurrentModel",
    "WallboxDataModel",
]
