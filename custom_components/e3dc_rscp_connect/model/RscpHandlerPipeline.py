"This file contains the RscpHandlerPipeline."

import logging  # noqa: I001
from .RscpModelInterface import RscpModelInterface
from ..e3dc.RscpValue import RscpValue  # noqa: TID252

_LOGGER = logging.getLogger(__name__)


class RscpHandlerPipeline:
    def __init__(self):
        self._handlers = []

    def add_handler(self, handler: RscpModelInterface):
        self._handlers.append(handler)

    async def process(self, values):
        """Process a list of RSCP values."""
        if values is None:
            _LOGGER.warning("Values is None, no data to process!")
            return

        for value in values:
            handled = False

            for handler in self._handlers:
                if handler.handle_rscp_data(value):
                    handled = True
                    break

            if not handled:
                _LOGGER.warning(
                    "Unhandled RSCP tag: %s Handlers: %d",
                    value.getTagName(),
                )

    async def collect_tags(self) -> list[RscpValue]:
        """Collect rscp tags from all registered handlers."""

        all_tags = []
        for handler in self._handlers:
            tags = handler.get_rscp_tags()
            all_tags.extend(tags)

        return all_tags
