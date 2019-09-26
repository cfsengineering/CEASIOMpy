import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def _set_limits(ax, data_field):
    """
    Adjust the plot limits for an axis object

    Args:
        :ax: (obj) Matplotlib axes object
        :data_fields: (dict) Either load or deformation fields
    """

    limits = {
        'x': [-0.01, 0.01],
        'y': [-0.01, 0.01],
        'z': [-0.01, 0.01],
    }

    xyz = data_field[:, 1:4]

    for coord, idx in zip('xyz', (0, 1, 2)):
        min_in_data = np.amin(xyz[:, idx])
        max_in_data = np.amax(xyz[:, idx])

        if min_in_data < limits[coord][0]:
            limits[coord][0] = min_in_data

        if max_in_data > limits[coord][1]:
            limits[coord][1] = max_in_data

    # Adjust the limits
    ax.set_xlim(*limits['x'])
    ax.set_ylim(*limits['y'])
    ax.set_zlim(*limits['z'])
    ax.set_aspect('equal')
    _set_equal_aspect_3D(ax)


def _set_equal_aspect_3D(ax):
    """
    Set aspect ratio of plot correctly

    Args:
        :ax: (obj) Matplotlib axes object
    """
    # See https://stackoverflow.com/a/19248731

    extents = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
    sz = extents[:, 1] - extents[:, 0]
    centers = np.mean(extents, axis=1)
    maxsize = max(abs(sz))
    r = maxsize/2
    for ctr, dim in zip(centers, 'xyz'):
        getattr(ax, 'set_{}lim'.format(dim))(ctr - r, ctr + r)



data = np.loadtxt('deformed_mesh.dat', delimiter='\t', skiprows=1)

fig = plt.figure(figsize=(10, 10))
ax = fig.gca(projection='3d')

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

x = data[:, 1]
y = data[:, 2]
z = data[:, 3]
ax.scatter(x, y, z)

_set_limits(ax, data)

plt.show()
