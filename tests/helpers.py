"""Small synchronization helpers for background lifecycle workers."""

import time


def wait_until(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("condition was not reached before timeout")


def wait_registered(extension, app, expected=True, timeout=2.0):
    wait_until(
        lambda: (
            extension.get_status(app)["operation_running"] is False
            and extension.get_status(app)["registered"] is expected
        ),
        timeout=timeout,
    )

