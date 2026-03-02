# Imports

from typing import Callable

from ceasiompy import log


# Functions

def progress_update(
    progress_callback: Callable[..., None] | None,
    *,
    detail: str | None = None,
    progress: float | None = None,
) -> None:
    if progress_callback is None:
        return None

    log.info(detail)
    progress_callback(
        detail=detail,
        progress=progress,
    )
