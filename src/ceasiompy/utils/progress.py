# Imports

from typing import Callable


# Functions

def progress_update(
    progress_callback: Callable[..., None] | None,
    *,
    detail: str | None = None,
    progress: float | None = None,
) -> None:
    if progress_callback is None:
        return
    progress_callback(
        detail=detail,
        progress=progress,
    )
