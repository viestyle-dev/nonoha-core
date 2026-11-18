"""Rate-limited logging of repeated failures.

A node that raises on every dispatch, or an app that sends malformed messages
at audio rate, must neither flood the log nor slow the event loop with a
traceback per event. ``ErrorLog`` logs the first occurrence in full and then
at most one line per interval with the count of what it left out.

Call it only on the failure path (inside ``except``): the normal path pays
nothing.
"""

from __future__ import annotations

import logging
import sys
import time


class ErrorLog:
    """One place that fails repeatedly (an endpoint, a timer, a tick)."""

    __slots__ = ("_logger", "_interval", "_next", "_suppressed", "_traced")

    def __init__(self, logger: logging.Logger, interval: float = 5.0):
        self._logger = logger
        self._interval = interval
        self._next = 0.0
        self._suppressed = 0
        self._traced = False

    def exception(self, message: str) -> None:
        """Log the exception being handled: with its traceback the first
        time, then one line per interval with the count left out."""
        now = time.monotonic()
        if now < self._next:
            self._suppressed += 1
            return
        self._next = now + self._interval
        if not self._traced:
            self._traced = True
            self._logger.error(message, exc_info=True)
            return
        error = sys.exc_info()[1]
        self._logger.error(
            "%s: %s: %s (%d more in the last %.0f s)",
            message,
            type(error).__name__,
            error,
            self._suppressed,
            self._interval,
        )
        self._suppressed = 0

    def warning(self, message: str) -> None:
        """Log a warning, then at most one per interval with the count left out."""
        now = time.monotonic()
        if now < self._next:
            self._suppressed += 1
            return
        self._next = now + self._interval
        if self._suppressed:
            self._logger.warning("%s (%d more in the last %.0f s)", message, self._suppressed, self._interval)
            self._suppressed = 0
        else:
            self._logger.warning(message)
