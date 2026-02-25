# Imports
import pytest

pytest.importorskip("openvsp")

from ceasiompy.vsp2cpacs.vsp2cpacs import main

from ceasiompy.utils.commonpaths import (
    VSP_DIR,
    WKDIR_PATH,
)

# Constants
VSP_FILES = sorted(VSP_DIR.glob("*.vsp3"))


@pytest.mark.parametrize("vsp_file", VSP_FILES, ids=[p.name for p in VSP_FILES])
def test_convert_all_vsp_geometries_to_cpacs(vsp_file):
    WKDIR_PATH.mkdir(exist_ok=True)
    main(str(vsp_file))
