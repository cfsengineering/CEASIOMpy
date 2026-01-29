# Imports
from ceasiompy.utils import get_module_status
from ceasiompy.utils.ceasiompyutils import get_install_path

from typing import Final
from pathlib import Path

# Constants
SOFTWARE_EXEC: Final[str] = "vsp"
SOFTWARE_NAME: Final[str] = "OpenVSP"
SOFTWARE_PATH: Final[Path | None] = get_install_path(
    SOFTWARE_EXEC,
    display_name=SOFTWARE_NAME,
)

# ===== Module Status =====
MODULE_STATUS = get_module_status(
    default=False,
    needs_soft_name=SOFTWARE_EXEC,
)

# ===== Include GUI =====
INCLUDE_GUI = False
