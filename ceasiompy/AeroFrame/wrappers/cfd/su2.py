#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AeroFrame wrapper for SU2
"""

# Author: Aaron Dettmann

from collections import defaultdict
from pathlib import Path

import numpy as np
from aeroframe.interpol.translate import get_deformed_mesh
from aeroframe.templates.wrappers import AeroWrapper
from ceasiompy.SU2Run.su2run import run_SU2_fsi


class Wrapper(AeroWrapper):
    def __init__(self, root_path, shared, settings):
        super().__init__(root_path, shared, settings)

        # SU2 specific files
        self.paths = {}
        self.paths["d_calc"] = Path(self.root_path, "..", "temp")
        self.paths["f_config"] = Path(self.paths["d_calc"], "ToolInput.cfg")
        self.paths["f_loads"] = Path(self.paths["d_calc"], "force.csv")
        self.paths["f_mesh"] = Path(self.paths["d_calc"], "ToolInput.su2")
        self.paths["f_disp"] = Path(self.paths["d_calc"], "disp.dat")

        # Make the working directory if it does not exist
        Path(self.paths["d_calc"]).mkdir(parents=True, exist_ok=True)

        self.first_iteration = True
        self.undeformed_mesh = None

    def _get_su2_load_array(self):
        """Return the load files as a array"""

        su2_load_array = np.genfromtxt(
            self.paths["f_loads"], delimiter=",", dtype=None, skip_header=1, encoding="latin1"
        )

        return su2_load_array

    def _get_load_fields(self, use_undeformed_POA=True):
        """
        Return AeroFrame load fields from SU2 results

        Returns:
            :load_fields: (dict) AeroFrame load fields
            :use_undeformed_POA: (bool) If True, *undeformed* points of attack
            will be used
        """

        su2_load_array = self._get_su2_load_array()

        load_fields = defaultdict(list)
        for row in su2_load_array:
            row = tuple(row)
            xyz_fxyz = np.concatenate((row[1:7], [0, 0, 0]))
            load_fields[str(row[-1])].append(xyz_fxyz)

        for component_uid, value in load_fields.items():
            value = np.array(value, dtype=float)

            # Replace the deformed POA
            if not self.first_iteration and use_undeformed_POA:
                value[:, 0:3] = self.undeformed_mesh[component_uid]

            load_fields[component_uid] = value

        return load_fields

    def _write_su2_disp_file(self):
        """Write the SU2 displacement file"""

        # Fetch the FEM deformation fields
        # def_fields = self.shared.structure.def_fields

        # TODO: make work for multiple wings
        orig_mesh = self.undeformed_mesh["Wing"]
        def_field = self.shared.structure.def_fields["Wing"]

        def_mesh = get_deformed_mesh(orig_mesh, def_field)

        # Indices and displacements at discrete mesh points
        num_mesh_points = orig_mesh.shape[0]
        idx = np.arange(start=0, stop=num_mesh_points, step=1).reshape((num_mesh_points, 1))
        u_xyz = def_mesh - orig_mesh

        # Write the displacement file
        header = f"{num_mesh_points}\t2\t1\t0"
        output_data = np.block([idx, orig_mesh + u_xyz])
        fmt = ["%d"] + ["%.10e" for _ in range(3)]
        np.savetxt(self.paths["f_disp"], output_data, fmt=fmt, delimiter="\t", header=header)

    def run_analysis(self, turn_off_deform=False):
        """
        Run the PyTornado analysis

        Args:
            :turn_off_deform: Flag which can be used to turn off all deformations
        """

        # Hint: If there is no displacement file, no deformation will be
        # taken into account
        if turn_off_deform:
            if self.paths["f_disp"].exists():
                pass

        else:
            self._write_su2_disp_file()

        # ----- Run the SU2 analysis -----
        run_SU2_fsi(
            config_path=self.paths["f_config"],
            wkdir=self.paths["d_calc"],
        )

        # Get the undeformed mesh in the first
        if self.first_iteration:
            load_fields = self._get_load_fields()
            self.undeformed_mesh = {}
            for component_uid, value in load_fields.items():
                self.undeformed_mesh[component_uid] = value[:, 0:3]

        # ----- Share load data -----
        self.shared.cfd.load_fields = self._get_load_fields()

        self.first_iteration = False

    def clean(self):
        """Clean method"""

        pass
