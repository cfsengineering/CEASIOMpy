"""
Shape_optimization.py

"""

# Library imports
from pathlib import Path
import sys, subprocess, os, logging
from cpacspy.cpacspy import CPACS  
import numpy as np
import textwrap
import shutil




# ────────────────────────── USER-TUNABLE “CONSTANTS” ──────────────────────────
BASE_CPACS  = Path("D150_simple.xml")   # default baseline file
WING_UID    = "Wing1"
SECTION_UIDS = [f"{WING_UID}_Sec{i}" for i in range(1, 5)]
LOGFMT      = "%(levelname)-8s  %(message)s"
logging.basicConfig(level=logging.INFO, format=LOGFMT)
LOG = logging.getLogger(__name__)
# ───────────────────────────────────────────────────────────────────────────────


# ═════════════════════ CPACS I/O ═════════════════════

def read_wing_params(cpacs: Path) -> np.ndarray:
    tx = CPACS(cpacs).tixi
    
    scalings_x = [tx.getDoubleElement(
        f"/cpacs/vehicles/aircraft/model/wings/wing[@uID='{WING_UID}']"
        f"/sections/section[@uID='{uid}']/transformation/scaling/x")
        for uid in SECTION_UIDS]
    
    scalings_y = [tx.getDoubleElement(
        f"/cpacs/vehicles/aircraft/model/wings/wing[@uID='{WING_UID}']"
        f"/sections/section[@uID='{uid}']/transformation/scaling/y")
        for uid in SECTION_UIDS]
    
    scalings_z = [tx.getDoubleElement(
        f"/cpacs/vehicles/aircraft/model/wings/wing[@uID='{WING_UID}']"
        f"/sections/section[@uID='{uid}']/transformation/scaling/z")
        for uid in SECTION_UIDS]
    
    rotations_y = [tx.getDoubleElement(
        f"/cpacs/vehicles/aircraft/model/wings/wing[@uID='{WING_UID}']"
        f"/sections/section[@uID='{uid}']/transformation/rotation/y")
        for uid in SECTION_UIDS]
    
    translations_x = [tx.getDoubleElement(
        f"/cpacs/vehicles/aircraft/model/wings/wing[@uID='{WING_UID}']"
        f"/sections/section[@uID='{uid}']/transformation/translation/x")
        for uid in SECTION_UIDS]
    
    translations_y = [tx.getDoubleElement(
        f"/cpacs/vehicles/aircraft/model/wings/wing[@uID='{WING_UID}']"
        f"/sections/section[@uID='{uid}']/transformation/translation/y")
        for uid in SECTION_UIDS]
    
    translations_z = [tx.getDoubleElement(
        f"/cpacs/vehicles/aircraft/model/wings/wing[@uID='{WING_UID}']"
        f"/sections/section[@uID='{uid}']/transformation/translation/z")
        for uid in SECTION_UIDS]
    
    return np.array([scalings_x, scalings_y, scalings_z, rotations_y, translations_x, translations_y, translations_z], float)

def read_flight_params(cpacs: Path) -> np.ndarray:
    cp = CPACS(cpacs)
    tx = cp.tixi
    
    altitude_vec = tx.getTextElement(
        "/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/"
        "aeroMap[1]/aeroPerformanceMap/altitude")
    
    mach_vec = tx.getTextElement(
        "/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/"
        "aeroMap[1]/aeroPerformanceMap/machNumber")
    
    AoA_vec = tx.getTextElement(
        "/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/"
        "aeroMap[1]/aeroPerformanceMap/angleOfAttack")
    
    AoS_vec = tx.getTextElement(
        "/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/"
        "aeroMap[1]/aeroPerformanceMap/angleOfSideslip")
    
    altitude = np.fromstring(altitude_vec, sep=';')
    mach = np.fromstring(mach_vec, sep=';')
    AoA = np.fromstring(AoA_vec, sep=';')
    AoS = np.fromstring(AoS_vec, sep=';')

    # if AoA.size < 2:
    #     raise ValueError("AoA must contain at least two values.")
    # if altitude.size < 2:
    #     raise ValueError("Altitude must contain at least two values.") 
    # if mach.size < 2:
    #     raise ValueError("Mach number must contain at least two values.")
    # if AoS.size < 2:    
    #     raise ValueError("AoS must contain at least two values.")
    
    return AoA, altitude, mach, AoS

def ensure_path(tx, xpath: str) -> None:
    """
    Ensure that every node except the last in `xpath`
    exists. Example:  ensure_path(tixi, '/cpacs/a/b/c')
    creates /a, /a/b, /a/b/c if they don't exist yet.
    """
    parts = xpath.strip("/").split("/")[1:]          # skip leading 'cpacs'
    current = "/cpacs"
    for step in parts:
        current = f"{current}/{step}"
        if not tx.checkElement(current):
            parent, name = current.rsplit("/", 1)
            tx.createElement(parent, name)

def next_workflow_number(wkdir_root: Path) -> int:
    """
    Return 1 + the highest integer suffix already present in
    WKDIR/Workflow_###.  If none exist, return 1.
    """
    nums = []
    for d in wkdir_root.glob("Workflow_*"):
        try:
            nums.append(int(d.name.split("_")[1]))
        except (IndexError, ValueError):
            pass
    return max(nums) + 1 if nums else 1

def write_cpacs(src: Path, dst: Path,
                twists: np.ndarray, AoA: np.ndarray) -> None:
    """
    -> copies `src` --> `dst`
    -> writes the four twist angles (y-rotation) into Wing1_Sec1..4
    -> writes the AoA into the aeroMap
    -> keeps a copy of that AoA under /toolspecific/…/Table/aoa
    """

    cp = CPACS(src)
    tx = cp.tixi

    # ── 1. twists (unchanged part) ─────────────────────────────────────
    for uid, tw in zip(SECTION_UIDS, twists):
        y = (f"/cpacs/vehicles/aircraft/model/wings/wing[@uID='{WING_UID}']"
             f"/sections/section[@uID='{uid}']/transformation/rotation/y")
        if tx.checkElement(y):
            tx.updateDoubleElement(y, float(tw), "%g")
        else:
            tx.addDoubleElement(y.rsplit("/", 1)[0], "y", float(tw), "%g")

    # ── 2.  Aeromap_aoaSweep  ──────────────────────────────────────────
    perf = ("/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/"
            "aeroMap[1]/aeroPerformanceMap")
    
    def all_parameters(tag: str):
        path = f"{perf}/{tag}"
        if tx.checkElement(path):
            parameter = tx.getTextElement(path)
            tx.updateTextElement(path, parameter)

    for tag in ("altitude", "machNumber", "angleOfSideslip"):
        all_parameters(tag)
    
    # ── 3. make sure /toolspecific/CEASIOMpy/avl/Table/aoa exists ──────
    tbl = "/cpacs/toolspecific/CEASIOMpy/avl/Table"
    if not tx.checkElement(tbl):
        if not tx.checkElement("/cpacs/toolspecific"):
            tx.createElement("/cpacs", "toolspecific")
        if not tx.checkElement("/cpacs/toolspecific/CEASIOMpy"):
            tx.createElement("/cpacs/toolspecific", "CEASIOMpy")
        if not tx.checkElement("/cpacs/toolspecific/CEASIOMpy/avl"):
            tx.createElement("/cpacs/toolspecific/CEASIOMpy", "avl")
        tx.createElement("/cpacs/toolspecific/CEASIOMpy/avl", "Table")

    aoa_node = f"{tbl}/aoa"
    if tx.checkElement(aoa_node):
        tx.updateTextElement(aoa_node, f"{AoA}")
    else:
        tx.addTextElement(tbl, "aoa", f"{AoA}")
        tx.addTextAttribute(aoa_node, "mapType", "vector")

    cp.save_cpacs(dst)



# ═════════════════════ pyAVL I/O ═════════════════════

def run_pyavl(cpacs_file: Path, opt_dir: Path) -> Path:
    """
    Run a pyAVL simulation based on the CPACS file `D150_simple.xml`.
    Store results in `output_dir` and return the path to the results file).
    """

    print(f"→ Running pyAVL with CPACS file {cpacs_file}")

    root = opt_dir.parent               # /CEASIOMpy
    wk_root = root / "WKDIR"
    wk_root.mkdir(exist_ok=True)
    # before = {d.name for d in wk_root.glob("Workflow_*")}

    workflow_num = next_workflow_number(wk_root)
    wf_name = f"Workflow_{workflow_num:03d}"  # es. Workflow_001, Workflow_002,...
    print(f"✔ Preparing to save PyAVL results in {wf_name}")

    # run CEASIOMpy
    proc = subprocess.run(
        ["ceasiompy_run", "-m", str(cpacs_file), "PyAVL"],
        cwd=root, capture_output=True, text=True,
    )
    if proc.returncode:
        print("\nCEASIOMpy / PyAVL failed:\n",
              textwrap.indent(proc.stdout + proc.stderr, "|  "))
        raise RuntimeError("PyAVL exited with non-zero status")
    
    # detect the newcomer 

    # diff = {d.name for d in wk_root.glob("Workflow_*")} - before
    # if not diff:
    #     raise FileNotFoundError("No new workflow directory found after pyAVL run.") # MODIFY: when is ready the loop put FileNotFoundError
    # wf_name = sorted(diff)[-1] # get the latest workflow
    # print(f"✔ PyAVL results in {wf_name}")


    src = wk_root / wf_name

    dst = opt_dir / "WKDIR" / wf_name
    if not dst.exists():
        shutil.copytree(src, dst) # archive the whole workflow
    
    # --- ToolOutput.xml (nested or flat) --------------------------------
    nested = src / "01_PyAVL" / "ToolOutput.xml"
    flat   = src / "ToolOutput.xml"
    if nested.is_file():
        return nested
    if flat.is_file():
        return flat
    raise FileNotFoundError(
        f"ToolOutput.xml not found at {nested} or {flat}"
    )

# ═════════════════════ SU2 I/O ═════════════════════
def run_su2(cpacs_file: Path, opt_dir: Path) -> Path:
    """
    Run a SU2 simulation based on the CPACS file `D150_simple.xml`.
    Store results in `output_dir` and return the path to the results file).
    """

    print(f"→ Running SU2 with CPACS file {cpacs_file}")

    root = opt_dir.parent               # /CEASIOMpy
    wk_root = root / "WKDIR"
    wk_root.mkdir(exist_ok=True)
    # before = {d.name for d in wk_root.glob("Workflow_*")}

    workflow_num = next_workflow_number(wk_root)
    wf_name = f"Workflow_{workflow_num:03d}"  # es. Workflow_001, Workflow_002,...
    print(f"✔ Preparing to save SU2 results in {wf_name}")

    # run CPACS2GMSH
    print("→ Generating mesh with CPACS2GMSH")
    proc_gmsh = subprocess.run(
        ["ceasiompy_run", "-m", str(cpacs_file), "CPACS2GMSH"],
        cwd=root, capture_output=True, text=True,
    )
    if proc_gmsh.returncode:
        print("\nCEASIOMpy / CPACS2GMSH failed:\n",
              textwrap.indent(proc_gmsh.stdout + proc_gmsh.stderr, "|  "))
        raise RuntimeError("CPACS2GMSH exited with non-zero status")
    
    print("✔ Mesh generation completed.")

    # run SU2
    proc = subprocess.run(
        ["ceasiompy_run", "-m", str(cpacs_file), "SU2Run"],
        cwd=root, capture_output=True, text=True,
    )
    if proc.returncode:
        print("\nCEASIOMpy / SU2 failed:\n",
              textwrap.indent(proc.stdout + proc.stderr, "|  "))
        raise RuntimeError("SU2 exited with non-zero status")
    
    # detect the newcomer 

    # diff = {d.name for d in wk_root.glob("Workflow_*")} - before
    # if not diff:
    #     raise FileNotFoundError("No new workflow directory found after SU2 run.") # MODIFY: when is ready the loop put FileNotFoundError
    # wf_name = sorted(diff)[-1] # get the latest workflow
    # print(f"✔ SU2 results in {wf_name}")


    src = wk_root / wf_name

    dst = opt_dir / "WKDIR" / wf_name
    if not dst.exists():
        shutil.copytree(src, dst) # archive the whole workflow
    
    # --- ToolOutput.xml (nested or flat) --------------------------------
    nested = src / "01_SU2" / "ToolOutput.xml"
    flat   = src / "ToolOutput.xml"
    if nested.is_file():
        return nested
    if flat.is_file():
        return flat
    raise FileNotFoundError(
        f"ToolOutput.xml not found at {nested} or {flat}"
    )

def _scalar(text: str) -> float:
    """
    Return the first numeric value in a CPACS vector string.
    Works for delimiters ';' ',' whitespace or newline.
    """
    for token in text.replace("\n", " ").replace(",", ";").split(";"):
        token = token.strip()
        if token:
            return float(token.split()[0])
    raise ValueError("no numeric value found in CPACS field")


def coeffs(toolxml: Path) -> tuple[float, float, float]:
    cp = CPACS(toolxml)
    tx = cp.tixi
    base = "/cpacs/toolspecific/CEASIOMpy/avl/Table"
    cl  = _scalar(tx.getTextElement(base + "/cl"))
    cd  = _scalar(tx.getTextElement(base + "/cd"))
    cm  = _scalar(tx.getTextElement(base + "/cms"))   
    return cl, cd, cm



def main() -> None:
    # Read cpacs file from command line or use default
    cpacs_file = (Path(sys.argv[1]).resolve()
                  if len(sys.argv) > 1 else BASE_CPACS.resolve())
    
    output_dir = cpacs_file.parent / "results"
    output_dir.mkdir(exist_ok=True)
    

    # 1. Read parameters from actual CPACS
    LOG.info(f"Reading parameters from {cpacs_file}")
    wing_parameters = read_wing_params(cpacs_file)

    LOG.info(f"Reading flight parameters from {cpacs_file}")
    try:
        AoA, altitude, mach, AoS = read_flight_params(cpacs_file)
    except ValueError as e:
        LOG.error(f"Flight parameter validation error: {e}")
        return
    

    # # 2. Write new CPACS files modified
    # modified_cpacs = cpacs_file.parent / "modified.cpacs.xml"
    # LOG.info(f"Writing modified CPACS to {modified_cpacs}")
    # write_cpacs(cpacs_file, modified_cpacs, wing_parameters[3], AoA) # only twist angles and AoA
    

    # 3. Run pyAVL with CPACS
    try:
        tool_output_AVL = run_pyavl(cpacs_file, output_dir)
    except Exception as e:
        LOG.error(f"pyAVL run failed: {e}")
        return
    
    # 4. Extract results from pyAVL output
    cl, cd, cm = coeffs(tool_output_AVL)
    LOG.info(f"Aerodynamic coefficients from pyAVL:\n  C_L={cl:.4f}, C_D={cd:.4f}, C_M={cm:.4f}")

    # 5. Run SU2 with CPACS
    try:
        tool_output_SU2 = run_su2(cpacs_file, output_dir)
    except Exception as e:
        LOG.error(f"SU2 run failed: {e}")
        return
    
    # 6. Extract results from SU2 output
    cl, cd, cm = coeffs(tool_output_SU2)
    LOG.info(f"Aerodynamic coefficients from SU2:\n  C_L={cl:.4f}, C_D={cd:.4f}, C_M={cm:.4f}")

if __name__ == "__main__":
    main()
