"""ErrorLog: the first failure in full, then one line per interval."""

import logging

from nonoha_core import error_log
from nonoha_core.error_log import ErrorLog


def test_first_with_traceback_then_counted(caplog, monkeypatch):
    now = [100.0]
    monkeypatch.setattr(error_log.time, "monotonic", lambda: now[0])
    log = ErrorLog(logging.getLogger("test.errors"), interval=5.0)
    with caplog.at_level("ERROR"):
        for _ in range(1000):
            try:
                raise ValueError("bad value")
            except ValueError:
                log.exception("node X failed")
        now[0] += 6.0
        try:
            raise ValueError("bad value")
        except ValueError:
            log.exception("node X failed")
    records = [r for r in caplog.records if r.name == "test.errors"]
    assert len(records) == 2
    assert records[0].exc_info is not None
    assert records[1].exc_info is None and "999 more" in records[1].getMessage()


def test_warnings_are_rate_limited(caplog, monkeypatch):
    now = [0.0]
    monkeypatch.setattr(error_log.time, "monotonic", lambda: now[0])
    log = ErrorLog(logging.getLogger("test.warnings"), interval=5.0)
    with caplog.at_level("WARNING"):
        for _ in range(10):
            log.warning("port not found")
        now[0] += 5.0
        log.warning("port not found")
    messages = [r.getMessage() for r in caplog.records if r.name == "test.warnings"]
    assert messages == ["port not found", "port not found (9 more in the last 5 s)"]
