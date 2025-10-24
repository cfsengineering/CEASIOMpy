"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This script estimates the maximum take of mass from a database
of conventional aircraft using the k-nearest neighbors regression method.

| Author : Aidan Jungo
| Date of creation: 2022-11-08

"""

# =================================================================================================
#   IMPORT
# =================================================================================================

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from ceasiompy import log
from ceasiompy.utils.commonnames import MTOM_FIGURE_NAME
from ceasiompy import MODULES_DIR_PATH
from sklearn.neighbors import KNeighborsRegressor


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def estimate_mtom(fuselage_length, fuselage_width, wing_area, wing_span, results_dir):
    """Function that estimates the Maximum Take-Off Mass from k-nearest neighbors regression
    based on geometric parameters.

    Args:
        fuselage_length (float): Fuselage length [m]
        fuselage_width (float): Fuselage width [m]
        wing_area (float): Main wing area [m^2]
        wing_span (float): Main wing span [m]
        results_dir (Path): Path to the directory where the results will be saved

    Returns:
        mtom (float): Maximum Take-Off Mass [kg].

    """

    log.info("MTOM KNNregression")

    aircraft_data_file_name = Path(
        MODULES_DIR_PATH, "WeightConventional", "files", "AircraftData2018_v3_ste.csv"
    )

    log.info(f"Open {aircraft_data_file_name}")
    aircraft_data = pd.read_csv(aircraft_data_file_name, index_col=0, header=None).T

    aircraft_df = aircraft_data[
        ["Wing_Span_m", "Wing_Area_m2", "Fus_Length_m", "Fus_Width_m", "MTOM"]
    ].astype(float)

    x_train = aircraft_df[["Fus_Length_m", "Fus_Width_m", "Wing_Area_m2", "Wing_Span_m"]]
    y_train = aircraft_df["MTOM"]

    knn_model = KNeighborsRegressor(n_neighbors=2, weights="distance")
    knn_model.fit(x_train.values, y_train.values)

    mtom = knn_model.predict([[fuselage_length, fuselage_width, wing_area, wing_span]])[0]

    fig = plt.figure()
    ax1 = plt.subplot(2, 2, 1)
    ax1.scatter(aircraft_df["Fus_Length_m"], aircraft_df["MTOM"])
    ax1.scatter(fuselage_length, mtom)
    ax1.set(xlabel="Fuselage lenght [m]", ylabel="MTOM [kg]")
    ax1.grid()

    ax2 = plt.subplot(2, 2, 2)
    ax2.scatter(aircraft_df["Fus_Width_m"], aircraft_df["MTOM"])
    ax2.scatter(fuselage_width, mtom)
    ax2.set(xlabel="Fuselage width [m]", ylabel="MTOM [kg]")
    ax2.grid()

    ax3 = plt.subplot(2, 2, 3)
    ax3.scatter(aircraft_df["Wing_Area_m2"], aircraft_df["MTOM"])
    ax3.scatter(wing_area, mtom)
    ax3.set(xlabel="Wing area [m2]", ylabel="MTOM [kg]")
    ax3.grid()

    ax4 = plt.subplot(2, 2, 4)
    ax4.scatter(aircraft_df["Wing_Span_m"], aircraft_df["MTOM"])
    ax4.scatter(wing_span, mtom)
    ax4.set(xlabel="Wing span [m]", ylabel="MTOM [kg]")
    ax4.grid()

    mtom_figure = Path(results_dir, MTOM_FIGURE_NAME)
    fig.suptitle("MTOM prediction")
    fig.tight_layout()
    plt.savefig(mtom_figure)

    if mtom <= 0:
        raise Exception(
            "Wrong mass estimation, unconventional aircraft "
            + "studied using the conventional aircraft database."
        )

    return mtom
