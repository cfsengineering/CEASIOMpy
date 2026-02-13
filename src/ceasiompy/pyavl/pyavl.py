"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to run AVL calculations in CEASIOMpy.
AVL allows to perform aerodynamic analyses using the vortex-lattice method (VLM).
"""

# Imports
import time

from concurrent.futures import wait
from ceasiompy.pyavl.func.plot import convert_ps_to_pdf
from ceasiompy.pyavl.func.results import get_avl_results
from ceasiompy.utils.referencevalues import get_ref_values
from ceasiompy.pyavl.func.avllog import estimate_case_progress_from_log
from ceasiompy.utils.ceasiompyutils import (
    has_display,
    run_software,
    get_sane_max_cpu,
)
from ceasiompy.pyavl.func.utils import (
    duplicate_elements,
)
from ceasiompy.pyavl.func.config import (
    get_command_path,
    write_command_file,
    retrieve_gui_values,
)

from pathlib import Path
from typing import Callable
from cpacspy.cpacspy import CPACS
from ceasiompy.pyavl.func.data import AVLData
from concurrent.futures import ProcessPoolExecutor

from concurrent.futures import FIRST_COMPLETED
from ceasiompy.pyavl import (
    SOFTWARE_NAME,
)


# Main

def run_case(case_dir_path: Path) -> None:
    '''
    Runs the created avl cases separately on 1 CPU.
    '''
    run_software(
        software_name=SOFTWARE_NAME,
        arguments=[""],
        wkdir=case_dir_path,
        with_mpi=False,
        stdin=open(str(get_command_path(case_dir_path)), "r"),
        xvfb=True,
    )
    if has_display():
        convert_ps_to_pdf(case_dir_path)


def main(
    cpacs: CPACS,
    results_dir: Path,
    progress_callback: Callable[..., None] | None = None,
) -> None:
    """
    Run AVL calculations on specified CPACS file.
        1. Load the necessary data.
        2. Run avl with p, q, r rate deflections.
        3. Run avl with control surfaces deflections.
    """

    # Store list of arguments for each case
    case_args = []

    (
        alt_list,
        mach_list,
        aoa_list,
        aos_list,
        rotation_rate_list,
        control_surface_list,
        avl_path,
        expand,
    ) = retrieve_gui_values(cpacs, results_dir)

    #
    # 2. p, q, r
    (
        new_alt_list,
        new_mach_list,
        new_aoa_list,
        new_aos_list,
        new_pitch_rate_list,
        new_roll_rate_list,
        new_yaw_rate_list,
    ) = duplicate_elements(
        False,
        alt_list,
        mach_list,
        aoa_list,
        aos_list,
        rotation_rate_list,
    )
    first_cases = len(new_alt_list)

    ref_area, ref_length = get_ref_values(cpacs)

    for i_case, altitude in enumerate(new_alt_list):
        avl_data = AVLData(
            ref_area=ref_area,
            ref_length=ref_length,

            altitude=altitude,
            mach=new_mach_list[i_case],
            alpha=new_aoa_list[i_case],
            beta=new_aos_list[i_case],

            p=new_pitch_rate_list[i_case],
            q=new_roll_rate_list[i_case],
            r=new_yaw_rate_list[i_case],
        )

        case_dir_path = write_command_file(
            i_case=i_case,
            avl_path=avl_path,
            avl_data=avl_data,
            results_dir=results_dir,
        )

        # Same AVL Configuration Parameters
        avl_data.save_json(json_path=case_dir_path / "avldata.json")

        case_args.append(case_dir_path)

    if control_surface_list != [0.0]:

        #
        # 3. aileron, elevator, rudder
        (
            new_alt_list,
            new_mach_list,
            new_aoa_list,
            new_aileron_list,
            new_elevator_list,
            new_rudder_list,
        ) = duplicate_elements(
            expand,
            alt_list,
            mach_list,
            aoa_list,
            control_surface_list,
        )

        # Iterate through each case
        for i_case, altitude in enumerate(new_alt_list):
            avl_data = AVLData(
                ref_area=ref_area,
                ref_length=ref_length,

                altitude=altitude,
                mach=new_mach_list[i_case],
                alpha=new_aoa_list[i_case],
                beta=new_aos_list[i_case],

                rudder=new_rudder_list[i_case],
                aileron=new_aileron_list[i_case],
                elevator=new_elevator_list[i_case],
            )

            case_dir_path = write_command_file(
                i_case=i_case + first_cases,
                avl_path=avl_path,
                avl_data=avl_data,
                results_dir=results_dir,
            )

            # Same AVL Configuration Parameters
            avl_data.save_json(json_path=case_dir_path / "avldata.json")

            case_args.append(case_dir_path)

    total_cases = len(case_args)
    if progress_callback is not None:
        progress_callback(detail=f"Prepared {total_cases} AVL case(s).", progress=0.0)

    if not total_cases:
        raise ValueError("No AVL cases to run.")

    start_t = time.monotonic()
    completed = 0
    with ProcessPoolExecutor(max_workers=get_sane_max_cpu()) as executor:
        future_to_args = {executor.submit(run_case, args): args for args in case_args}

        while future_to_args:
            done, not_done = wait(
                future_to_args,
                timeout=0.5,
                return_when=FIRST_COMPLETED,
            )

            if progress_callback is not None:
                active_log_path: Path | None = None
                active_case_progress = 0.0
                active_case_label = "running"
                active_case_name: str | None = None
                if not_done:
                    some_future = next(iter(not_done))
                    case_dir_path = Path(future_to_args[some_future])
                    active_log_path = case_dir_path / f"logfile_{SOFTWARE_NAME}.log"
                    active_case_progress, active_case_label = estimate_case_progress_from_log(
                        active_log_path
                    )
                    active_case_name = case_dir_path.name

                elapsed_s = time.monotonic() - start_t
                overall_progress = (
                    (completed + active_case_progress) / total_cases if total_cases else 0.0
                )

                progress_callback(
                    detail=(
                        f"Running AVL cases ({completed}/{total_cases})…"
                        + (
                            f" Current: {active_case_name} ({active_case_label})"
                            if active_case_name
                            else ""
                        )
                    ),
                    progress=overall_progress,
                    elapsed_seconds=elapsed_s,
                )

            for future in done:
                case_dir_path = Path(future_to_args.pop(future))
                try:
                    future.result()
                except Exception as exc:
                    if progress_callback is not None:
                        elapsed_s = time.monotonic() - start_t
                        progress_callback(
                            detail=f"AVL failed in {case_dir_path.name}: {exc}",
                            progress=(completed / total_cases) if total_cases else 0.0,
                            elapsed_seconds=elapsed_s,
                        )
                    raise

                completed += 1
                if progress_callback is not None:
                    elapsed_s = time.monotonic() - start_t
                    overall_progress = completed / total_cases if total_cases else 0.0
                    progress_callback(
                        detail=f"Completed {completed}/{total_cases}: {case_dir_path.name}",
                        progress=overall_progress,
                        elapsed_seconds=elapsed_s,
                    )

    if progress_callback is not None:
        progress_callback(detail="Collecting AVL results…", progress=1.0)

    get_avl_results(
        cpacs=cpacs,
        results_dir=results_dir,
    )

    if progress_callback is not None:
        progress_callback(detail="AVL results ready.", progress=1.0)
