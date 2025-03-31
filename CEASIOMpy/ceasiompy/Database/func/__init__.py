# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy import log
from ceasiompy.PyAVL import MODULE_NAME as PYAVL_NAME
# from ceasiompy.SU2Run import MODULE_NAME as SU2RUN_NAME
from ceasiompy.CPACS2GMSH import MODULE_NAME as CPACS2GMSH_NAME
from ceasiompy.DynamicStability import MODULE_NAME as DYNSTAB_NAME

# ==============================================================================
#   CONSTANTS
# ==============================================================================

# Tables structure of ceasiompy.db
TABLE_DICT = {
    f"{PYAVL_NAME}":
        [
            "avl_data",
            """
                aircraft TEXT,

                alt REAL,
                mach REAL,
                alpha REAL,
                beta REAL,

                pb_2V REAL,
                qc_2V REAL,
                rb_2V REAL,

                flap REAL,
                aileron REAL,
                elevator REAL,
                rudder REAL,

                xref REAL,
                yref REAL,
                zref REAL,

                cd REAL,
                cs REAL,
                cl REAL,

                cmd REAL,
                cms REAL,
                cml REAL,

                cmd_a REAL,
                cms_a REAL,
                cml_a REAL,

                cmd_b REAL,
                cms_b REAL,
                cml_b REAL,
            """
        ],
    f"{CPACS2GMSH_NAME}":
        [
            "gmsh_data",
            """
                aircraft TEXT,
                deformation TEXT,
                angle REAL,
                su2_file_data BLOB,
            """
        ],
    f"{DYNSTAB_NAME}":
        [
            "derivatives_data",
            """
                aircraft TEXT,

                method TEXT,

                chord INT,
                span INT,

                mach REAL,

                x_ref REAL,
                y_ref REAL,
                z_ref REAL,

                cm_alphaprim REAL,
                cz_alphaprim REAL,
                cx_alphaprim REAL,

                cy_betaprim REAL,
                cl_betaprim REAL,
                cn_betaprim REAL,
            """
        ],
}

# ==============================================================================
#    MAIN
# ==============================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
