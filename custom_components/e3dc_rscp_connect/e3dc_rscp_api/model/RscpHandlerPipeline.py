"This file contains the RscpHandlerPipeline."

import logging  # noqa: I001
from .RscpModelInterface import RscpModelInterface
from rscp_lib.RscpValue import RscpValue

_LOGGER = logging.getLogger(__name__)


class RscpHandlerPipeline:
    def __init__(self):
        self._handlers = []
        # tag names already reported as unhandled, so each one is only warned
        # about once instead of on every poll cycle
        self._unhandled_tags = set()

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
                self.__report_unhandled(value.getTagName())

    def __report_unhandled(self, tag_name):
        """Warns about an unhandled tag once, then keeps it at debug level."""
        if tag_name in self._unhandled_tags:
            _LOGGER.debug("Unhandled RSCP tag: %s", tag_name)
            return

        self._unhandled_tags.add(tag_name)
        _LOGGER.warning(
            "Unhandled RSCP tag: %s. Further occurrences are logged at debug level.",
            tag_name,
        )

    async def collect_tags(self) -> list[RscpValue]:
        """Collect rscp tags from all registered handlers."""

        all_tags = []
        for handler in self._handlers:
            tags = handler.get_rscp_tags()
            all_tags.extend(tags)

        return all_tags
