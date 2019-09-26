#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AeroFrame wrapper for SU2
"""

# Author: Aaron Dettmann

from collections import defaultdict
from os.path import join

import numpy as np
from aeroframe.templates.wrappers import AeroWrapper
from aeroframe.fileio.serialise import dump_json_def_fields

from ceasiompy.SU2Run.su2run import run_SU2_fsi

# config_path = MODULE_DIR + '/ToolInput/ToolInput.cfg'
# calculation_dir = os.getcwd() + '/temp'
# input_disp_path = MODULE_DIR + '/ToolInput/disp.dat'
#
# shutil.copy(input_disp_path,calculation_dir+'/disp.dat')
#
# run_SU2_fsi(config_path, calculation_dir)



class Wrapper(AeroWrapper):

    def __init__(self, root_path, shared, settings):
        super().__init__(root_path, shared, settings)

        # SU2 files
        self.own_files = {}
        # self.own_files['f_loads'] = join(self.root_path, 'cfd/forces_FlatPlate_2.csv')
        self.own_files['f_loads'] = join(self.root_path, 'cfd/force.csv')

        # TODO:
        # - Inititalise attribute for the undeformed CFD

    def run_analysis(self, turn_off_deform=False):
        """
        Run the PyTornado analysis

        Args:
            :turn_off_deform: Flag which can be used to turn off all deformations
        """

        if turn_off_deform:
            ...
        else:
            ...

        # ----- Run the SU2 analysis -----
        ...
        # =====
        if self.shared.structure.def_fields is not None:
            dump_json_def_fields("deformation_fields.json", self.shared.structure.def_fields)
        # =====

        # ----- Share load data -----
        load_fields = self._get_load_fields()
        self.shared.cfd.load_fields = load_fields

    def clean(self):
        """
        Clean method
        """

        ...

    def _get_load_fields(self):
        """
        Return AeroFrame load fields from SU2 results

        Returns:
            :load_fields: (dict) AeroFrame load fields
        """

        load_fields = _get_load_fields(self.own_files['f_loads'])
        return load_fields


def _get_load_fields(load_file):
    """
    Return AeroFrame load fields from SU2 results

    Returns:
        :load_fields: (dict) AeroFrame load fields
    """

    array = np.genfromtxt(load_file, delimiter=',', dtype=None, skip_header=1, encoding='latin1')

    load_fields = defaultdict(list)
    for row in array:
        row = tuple(row)
        xyz_fxyz = np.concatenate((row[1:7], [0, 0, 0]))
        load_fields[str(row[-1])].append(xyz_fxyz)

    for key, value in load_fields.items():
        load_fields[key] = np.array(value, dtype=float)

    return load_fields
