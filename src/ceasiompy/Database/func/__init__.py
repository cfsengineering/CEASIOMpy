# Imports

from ceasiompy.PyAVL import MODULE_NAME as PYAVL_NAME

# from ceasiompy.SU2Run import MODULE_NAME as SU2RUN_NAME
from ceasiompy.CPACS2GMSH import MODULE_NAME as CPACS2GMSH_NAME
from ceasiompy.DynamicStability import MODULE_NAME as DYNSTAB_NAME

# ==============================================================================
#   CONSTANTS
# ==============================================================================

# Tables structure of ceasiompy.db
TABLE_DICT = {
    f"{PYAVL_NAME}": [
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
        """,
    ],
    f"{CPACS2GMSH_NAME}": [
        "gmsh_data",
        """
            aircraft TEXT,
            deformation TEXT,
            angle REAL,
            su2_file_data BLOB,
        """,
    ],
    f"{DYNSTAB_NAME}_alpha": [
        "alpha_derivatives",
        """
            aircraft TEXT,

            method TEXT,

            chord INT,
            span INT,

            alt REAL,
            mach REAL,
            aoa REAL,
            aos REAL,

            x_ref REAL,
            y_ref REAL,
            z_ref REAL,

            cm_alphaprim REAL,
            cz_alphaprim REAL,
            cx_alphaprim REAL,
        """,
    ],
    f"{DYNSTAB_NAME}_beta": [
        "beta_derivatives",
        """
            aircraft TEXT,

            method TEXT,

            chord INT,
            span INT,

            alt REAL,
            mach REAL,
            aoa REAL,
            aos REAL,

            x_ref REAL,
            y_ref REAL,
            z_ref REAL,

            cy_betaprim REAL,
            cl_betaprim REAL,
            cn_betaprim REAL,
        """,
    ],
}

ALLOWED_TABLES = [value[0] for value in TABLE_DICT.values()]

TABLE_TO_MODULE = {item[0]: key for key, item in TABLE_DICT.items()}

ALLOWED_COLUMNS = {
    table: [
        line.strip().split()[0]  # Extract column names from the SQL-like definitions
        for line in TABLE_DICT[TABLE_TO_MODULE[table]][1].splitlines()
        if line.strip() and not line.strip().startswith("--")  # Ignore empty lines and comments
    ]
    for table in ALLOWED_TABLES
}

# How to extract aerodynamic coefficients in st.txt
PYAVL_ST = {
    "Alpha": (1, "alpha"),
    "Beta": (1, "beta"),
    "Mach": (1, "mach"),
    "pb/2V": (2, "pb_2V"),
    "qc/2V": (2, "qc_2V"),
    "rb/2V": (2, "rb_2V"),
    "flap": (1, "flap"),
    "aileron": (1, "aileron"),
    "elevator": (1, "elevator"),
    "rudder": (1, "rudder"),
    "Xref": (1, "xref"),
    "Yref": (2, "yref"),
    "Zref": (3, "zref"),
    "CDtot": (1, "cd"),
    "CYtot": (1, "cs"),
    "CLtot": (1, "cl"),
    "Cltot": (2, "cmd"),
    "Cmtot": (2, "cms"),
    "Cntot": (2, "cml"),
    "Cla": (1, "cmd_a"),
    "Cma": (1, "cms_a"),
    "Cna": (1, "cml_a"),
    "Clb": (2, "cmd_b"),
    "Cmb": (2, "cms_b"),
    "Cnb": (2, "cml_b"),
}

# pyavl.py
PYAVL_CTRLSURF = ["flap", "aileron", "elevator", "rudder"]
