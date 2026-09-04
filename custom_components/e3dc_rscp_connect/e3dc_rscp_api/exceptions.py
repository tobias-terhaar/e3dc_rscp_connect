"""Errors raised by the E3/DC RSCP api.

Callers of this package should never have to catch an exception of the
underlying ``rscp_lib`` protocol implementation, every error leaves the api
as one of the classes below.
"""


class E3dcRscpError(Exception):
    """Base class of all errors raised by this package."""


class E3dcConnectionError(E3dcRscpError):
    """The device could not be reached, or the connection was lost."""


class E3dcAuthenticationError(E3dcRscpError):
    """The device rejected the given username and password."""


class E3dcIdentificationError(E3dcRscpError):
    """The devices behind the connection could not be identified.

    Usually raised when the RSCP key does not match the one of the device, as
    the answers can then not be decrypted.
    """
