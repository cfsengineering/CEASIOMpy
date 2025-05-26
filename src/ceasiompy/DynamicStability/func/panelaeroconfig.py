"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Modified PanelAero methods, see: https://github.com/DLR-AE/PanelAero.
| Author: Leon Deligny
| Creation: 2025-01-27

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import matplotlib

import numpy as np
import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from ceasiompy import log

# =================================================================================================
#   BACKEND SETTING
# =================================================================================================

try:
    # Try to use TkAgg if DISPLAY is set and Tkinter is available
    if os.environ.get("DISPLAY", "") != "":
        matplotlib.use("TkAgg")
    else:
        matplotlib.use("Agg")
except Exception:
    # Fallback to Agg if TkAgg is not available or fails
    matplotlib.use("Agg")

# =================================================================================================
#   CLASSES
# =================================================================================================


class AeroModel:
    def __init__(self, wings_list):
        self.aerogrid = None
        self.caerocards = None
        self.wings_list = wings_list

    def build_aerogrid(self):
        caero_grid, caero_panels, caerocards = self.read_CAERO(0)
        ID = []
        length = []  # length of panel
        A = []  # area of one panel
        N = []  # unit normal vector
        offset_l = []  # 25% point l
        offset_k = []  # 50% point k
        offset_j = []  # 75% downwash control point j
        offset_P1 = []  # Vortex point at 25% chord, 0% span
        offset_P3 = []  # Vortex point at 25% chord, 100% span
        r = []  # vector P1 to P3, span of panel

        for i_panel in range(len(caero_panels["ID"])):

            #
            #                   l_2
            #             4 o---------o 3
            #               |         |
            #  u -->    b_1 | l  k  j | b_2
            #               |         |
            #             1 o---------o 2
            #         y         l_1
            #         |
            #        z.--- x

            indices = [
                np.where(caero_panels["cornerpoints"][i_panel][j] == caero_grid["ID"])[0][0]
                for j in range(4)
            ]

            l_1 = caero_grid["offset"][indices[1]] - caero_grid["offset"][indices[0]]
            l_2 = caero_grid["offset"][indices[2]] - caero_grid["offset"][indices[3]]
            b_1 = caero_grid["offset"][indices[3]] - caero_grid["offset"][indices[0]]
            b_2 = caero_grid["offset"][indices[2]] - caero_grid["offset"][indices[1]]
            l_m = (l_1 + l_2) / 2.0
            b_m = (b_1 + b_2) / 2.0

            ID.append(caero_panels["ID"][i_panel])
            length.append(l_m[0])
            # A.append(l_m[0]*b_m[1])
            A.append(np.linalg.norm(np.cross(l_m, b_m)))
            normal = np.cross(l_1, b_1) / np.linalg.norm(np.cross(l_1, b_1))
            if normal[2] < 0.0:
                normal = -normal
            N.append(normal)
            offset_l.append(caero_grid["offset"][indices[0]] + 0.25 * l_m + 0.50 * b_1)
            offset_k.append(caero_grid["offset"][indices[0]] + 0.50 * l_m + 0.50 * b_1)
            offset_j.append(caero_grid["offset"][indices[0]] + 0.75 * l_m + 0.50 * b_1)
            offset_P1.append(caero_grid["offset"][indices[0]] + 0.25 * l_1)
            offset_P3.append(caero_grid["offset"][indices[3]] + 0.25 * l_2)
            r.append(
                (caero_grid["offset"][indices[3]] + 0.25 * l_2)
                - (caero_grid["offset"][indices[0]] + 0.25 * l_1)
            )

        n = len(ID)
        arange = np.arange(n * 6).reshape((n, 6))
        set_l, set_k, set_j = arange, arange, arange

        # Assure corner points are correctly generated
        if not isinstance(caero_grid["ID"], np.ndarray):
            raise TypeError("'caero_grid['ID']' must be a NumPy array.")
        if caero_grid["ID"].ndim != 1:
            raise ValueError("'caero_grid['ID']' must be a 1D array.")
        if caero_grid["ID"].shape[0] != caero_grid["offset"].shape[0]:
            raise ValueError("'ID' and 'offset' must have the same number of rows.")

        reshaped_id = np.reshape(caero_grid["ID"], (-1, 1))
        corner_points = np.hstack(reshaped_id, caero_grid["offset"])

        aerogrid = {
            "ID": np.array(ID),
            "l": np.array(length),
            "A": np.array(A),
            "N": np.array(N),
            "offset_l": np.array(offset_l),
            "offset_k": np.array(offset_k),
            "offset_j": np.array(offset_j),
            "offset_P1": np.array(offset_P1),
            "offset_P3": np.array(offset_P3),
            "r": np.array(r),
            "set_l": set_l,
            "set_k": set_k,
            "set_j": set_j,
            "CD": caero_panels["CD"],
            "CP": caero_panels["CP"],
            "n": n,
            "coord_desc": "bodyfixed",
            "cornerpoint_panels": caero_panels["cornerpoints"],
            "cornerpoint_grids": corner_points,
        }

        self.aerogrid = aerogrid
        self.caerocards = caerocards

    def read_CAERO(self, i_file):
        caerocards = []

        # TODO: Improve the quality of aerocards by admitting several CPACS sections

        for wing_i in self.wings_list:

            caerocard = {
                "EID": 2 * int(wing_i["EID"]) + 1,  # int
                "CP": int(wing_i["CP"]),  # int
                "n_span": int(wing_i["n_span"]),  # int
                "n_chord": int(wing_i["n_chord"]),  # int
                "X1": wing_i["X1"],  # np.array([float, float, float])
                "length12": wing_i["length12"],  # float
                "X4": wing_i["X4"],  # np.array([float, float, float])
                "length43": wing_i["length43"],  # float
                "X2": wing_i["X1"] + np.array([wing_i["length12"], 0.0, 0.0]),
                "X3": wing_i["X4"] + np.array([wing_i["length43"], 0.0, 0.0]),
            }

            X1 = np.array([wing_i["X4"][0], -wing_i["X4"][1], wing_i["X4"][2]])
            caerocard_sym = {
                "EID": 2 * int(wing_i["EID"]),  # int
                "CP": int(wing_i["CP"]),  # int
                "n_span": int(wing_i["n_span"]),  # int
                "n_chord": int(wing_i["n_chord"]),  # int
                # Left to right
                "X1": X1,
                "length12": wing_i["length43"],  # float
                # Symmetry in x-z plane
                "X4": wing_i["X1"],  # np.array([float, float, float])
                "length43": wing_i["length12"],  # float
                "X2": X1 + np.array([wing_i["length43"], 0.0, 0.0]),
                "X3": wing_i["X1"] + np.array([wing_i["length12"], 0.0, 0.0]),
            }

            caerocards.append(caerocard_sym)
            caerocards.append(caerocard)

        # from CAERO cards, construct corner points... '
        # then, combine four corner points to one panel
        grid_ID = i_file * 100000  # the file number is used to set a range of grid IDs
        grids = {"ID": [], "offset": []}
        panels = {"ID": [], "CP": [], "CD": [], "cornerpoints": []}

        for caerocard in caerocards:
            # calculate LE, Root and Tip vectors [x,y,z]^T
            LE = caerocard["X4"] - caerocard["X1"]
            Root = caerocard["X2"] - caerocard["X1"]
            Tip = caerocard["X3"] - caerocard["X4"]

            if caerocard["n_chord"] == 0:
                print("AEFACT cards are not supported by this reader.")
            else:
                # assume equidistant spacing
                d_chord = np.linspace(0.0, 1.0, caerocard["n_chord"] + 1)

            if caerocard["n_span"] == 0:
                print("AEFACT cards are not supported by this reader.")
            else:
                # assume equidistant spacing
                d_span = np.linspace(0.0, 1.0, caerocard["n_span"] + 1)

            #######################################################################################
            # Building matrix of corner points
            #######################################################################################

            # Instantiate the grid of size n_chord x n_span
            grids_map = np.zeros((caerocard["n_chord"] + 1, caerocard["n_span"] + 1), dtype="int")

            for i_strip in range(caerocard["n_span"] + 1):
                for i_row in range(caerocard["n_chord"] + 1):
                    # Define offset
                    offset = (
                        caerocard["X1"]
                        + LE * d_span[i_strip]
                        + (Root * (1.0 - d_span[i_strip]) + Tip * d_span[i_strip]) * d_chord[i_row]
                    )
                    grids["offset"].append(offset)

                    grids["ID"].append(grid_ID)
                    grids_map[i_row, i_strip] = grid_ID

                    grid_ID += 1

            # build panels from cornerpoints
            # index based on n_boxes
            panel_ID = caerocard["EID"]
            for i_strip in range(caerocard["n_span"]):
                for i_row in range(caerocard["n_chord"]):
                    panels["ID"].append(panel_ID)
                    panels["CP"].append(caerocard["CP"])  # applying CP of CAERO card to all grids
                    panels["CD"].append(caerocard["CP"])
                    panels["cornerpoints"].append(
                        [
                            grids_map[i_row, i_strip],
                            grids_map[i_row + 1, i_strip],
                            grids_map[i_row + 1, i_strip + 1],
                            grids_map[i_row, i_strip + 1],
                        ]
                    )

                    panel_ID += 1

        panels["ID"] = np.array(panels["ID"])
        panels["CP"] = np.array(panels["CP"])
        panels["CD"] = np.array(panels["CD"])
        panels["cornerpoints"] = np.array(panels["cornerpoints"])
        grids["ID"] = np.array(grids["ID"])
        grids["offset"] = np.array(grids["offset"])

        return grids, panels, caerocards


class DetailedPlots:

    def __init__(self, model):
        self.model = model

    def plot_aerogrid(self, scalars=None, colormap="plasma"):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        for shell in self.model.aerogrid["cornerpoint_panels"]:
            vertices = [self.model.aerogrid["cornerpoint_grids"][id, 1:] for id in shell]
            poly = Poly3DCollection([vertices], alpha=0.5)
            if scalars is not None:
                poly.set_array(np.array(scalars))
                poly.set_cmap(colormap)
            ax.add_collection3d(poly)

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")

        # Set axis limits to zoom out and make the plot a cube
        all_points = self.model.aerogrid["cornerpoint_grids"][:, 1:]
        max_range = (
            max(
                all_points[:, 0].max() - all_points[:, 0].min(),
                all_points[:, 1].max() - all_points[:, 1].min(),
                all_points[:, 2].max() - all_points[:, 2].min(),
            )
            * 0.5
        )

        mid_x = (all_points[:, 0].max() + all_points[:, 0].min()) * 0.5
        mid_y = (all_points[:, 1].max() + all_points[:, 1].min()) * 0.5
        mid_z = (all_points[:, 2].max() + all_points[:, 2].min()) * 0.5

        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)

        # Add a title to the plot
        ax.set_title("Aerogrid Visualization")

        plt.show()


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute.")
