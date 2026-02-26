# Imports
import pytest

from ceasiompy.vsp2cpacs.vsp2cpacs import main

from ceasiompy import log
from ceasiompy.utils.commonpaths import (
    VSP_DIR,
    WKDIR_PATH,
)


# Constants
VSP_FILES = sorted(VSP_DIR.glob("*.vsp3"))


# Tests

@pytest.mark.parametrize("vsp_file", VSP_FILES, ids=[p.name for p in VSP_FILES])
def test_convert_all_vsp_geometries_to_cpacs(vsp_file):
    WKDIR_PATH.mkdir(exist_ok=True)
    cpacs_file = main(
        vsp_file=str(vsp_file),
        output_dir=WKDIR_PATH,
    )
    log.info(f"Converted {vsp_file=} to {cpacs_file=}")


if __name__ == "__main__":
    for vsp_file in VSP_FILES:
        test_convert_all_vsp_geometries_to_cpacs(vsp_file)
