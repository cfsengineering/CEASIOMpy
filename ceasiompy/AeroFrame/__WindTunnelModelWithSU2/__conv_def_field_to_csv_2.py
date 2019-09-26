# For testing purposes
# --> Convert deformation field to CSV file

import numpy as np

from aeroframe.fileio.serialise import load_json_def_fields
from aeroframe.interpol.translate import get_deformed_mesh

# Original SU2 mesh
array = np.genfromtxt('cfd/force.csv', delimiter=',', dtype=None, skip_header=1, encoding='latin1')
orig_mesh = []
for row in array:
    row = tuple(row)
    xyz = row[1:4]
    orig_mesh.append(xyz)

orig_mesh = np.array(orig_mesh, dtype=float)

# Deformation field from FramAT
def_fields = load_json_def_fields('deformation_fields.json')
def_mesh = get_deformed_mesh(orig_mesh, def_fields['Wing'])

# Indices and displacements at discrete mesh points
idx = np.arange(start=0, stop=orig_mesh.shape[0], step=1)
idx = idx.reshape((orig_mesh.shape[0], 1))
idx = np.array(idx, dtype=int)
u_xyz = def_mesh - orig_mesh

# ============ TESTING: Multiply deformation by factor
u_xyz = u_xyz*10
# ============

header = f'{orig_mesh.shape[0]}\t2\t1\t0'
output_data = np.block([idx, orig_mesh+u_xyz])
fmt = ['%d'] + ['%.10e' for _ in range(3)]
np.savetxt("deformed_mesh.dat", output_data, fmt=fmt, delimiter='\t', header=header)
