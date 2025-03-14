# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import matplotlib.pyplot as plt
import matplotlib.tri as tri
import pandas as pd
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split
import numpy as np
from skopt.space import Real, Categorical
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import RS_XPATH, SM_XPATH, SMTRAIN_XPATH, PLOT_XPATH
from cpacspy.cpacsfunctions import (
    get_value_or_default,
    create_branch,
    add_value,
    get_value,
    open_tixi,
)
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS
from ceasiompy.SMUse.func.smUconfig import load_surrogate
from ceasiompy.SMTrain.func.smTfunc import make_predictions
from ceasiompy.utils.ceasiompyutils import get_results_directory, get_aeromap_list_from_xpath

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def plot_response_surface(cpacs_path):

    cpacs = CPACS(cpacs_path)
    tixi = open_tixi(cpacs_path)

    model, coefficient, removed_columns = load_surrogate(cpacs_path)

    if not isinstance(removed_columns, list):
        print("Warning: removed_columns is not a list, setting to empty list.")
        removed_columns = []

    input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

    x = get_value_or_default(cpacs.tixi, RS_XPATH + "/VariableOnX/Variable", "angleOfAttack")
    x_low_limit = get_value_or_default(cpacs.tixi, RS_XPATH + "/VariableOnX/LowLimit", "0.0")
    x_high_limit = get_value_or_default(cpacs.tixi, RS_XPATH + "/VariableOnX/HighLimit", "0.0")

    y = get_value_or_default(cpacs.tixi, RS_XPATH + "/VariableOnY/Variable", "machNumber")
    y_low_limit = get_value_or_default(cpacs.tixi, RS_XPATH + "/VariableOnY/LowLimit", "0.0")
    y_high_limit = get_value_or_default(cpacs.tixi, RS_XPATH + "/VariableOnY/HighLimit", "0.0")

    c1 = get_value_or_default(cpacs.tixi, RS_XPATH + "/FirstConstantVariable", "altitude")
    c1_value = get_value_or_default(cpacs.tixi, RS_XPATH + "/FirstConstantVariableValue", "10000")

    c2 = get_value_or_default(cpacs.tixi, RS_XPATH + "/SecondConstantVariable", "angleOfSideslip")
    c2_value = get_value_or_default(cpacs.tixi, RS_XPATH + "/SecondConstantVariableValue", "0")

    # Genera i punti della griglia
    x_grid = np.linspace(x_low_limit, x_high_limit, 50)
    y_grid = np.linspace(y_low_limit, y_high_limit, 50)
    X, Y = np.meshgrid(x_grid, y_grid)

    # Costruisce il vettore di input
    input_data = np.column_stack(
        [
            (
                X.ravel()
                if col == x
                else (
                    Y.ravel()
                    if col == y
                    else np.full(X.size, c1_value) if col == c1 else np.full(X.size, c2_value)
                )
            )
            for col in input_columns
            if col not in removed_columns
        ]
    )

    aeromap_for_scatter_xpath = PLOT_XPATH + "/aeroScatter"
    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, aeromap_for_scatter_xpath)

    # Creazione lista di DataFrame con colonna UID
    aeromap_df_list = []
    for aeromap_uid in aeromap_uid_list:
        aeromap_df = cpacs.get_aeromap_by_uid(aeromap_uid).df
        aeromap_df["uid"] = aeromap_uid
        aeromap_df_list.append(aeromap_df)

    # Concatenazione delle aeromap in un unico DataFrame
    full_aeromap_df = pd.concat(aeromap_df_list, ignore_index=True)

    # Predizioni
    pred_values, _ = make_predictions(model, input_data)
    Z = pred_values.reshape(X.shape)

    # Plot
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8)

    # Lista di simboli per lo scatter
    scatter_markers = ["o", "X", "s"]
    scatter_colors = ["r", "b", "g"]

    # Ciclo su ciascun aeromap_uid
    for idx, aeromap_uid in enumerate(aeromap_uid_list):
        aeromap_filtered = full_aeromap_df[full_aeromap_df["uid"] == aeromap_uid]

        # Applica il filtro su c1 e c2
        aeromap_filtered = aeromap_filtered[
            (aeromap_filtered[c1] == c1_value) & (aeromap_filtered[c2] == c2_value)
        ]

        log.info(f"Processing aeromap: {aeromap_uid}")

        if not aeromap_filtered.empty:
            x_scatter = aeromap_filtered[x].values
            y_scatter = aeromap_filtered[y].values
            coeff_scatter = aeromap_filtered[coefficient].values

            marker = scatter_markers[idx % len(scatter_markers)]
            color = scatter_colors[idx % len(scatter_colors)]
            ax.scatter(
                x_scatter, y_scatter, coeff_scatter, c=color, marker=marker, label=aeromap_uid
            )

    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_xlim(ax.get_xlim()[::-1])
    ax.set_ylim(ax.get_ylim()[::-1])
    ax.set_zlabel(f"{coefficient}")
    ax.set_title(f"Response Surface for {c1} = {c1_value} and {c2} = {c2_value}")
    ax.view_init(elev=25, azim=45)
    ax.legend()

    # Salvataggio del grafico come immagine
    results_dir = get_results_directory("SaveAeroCoefficients")
    fig_name = "response_surface_" + x + "_vs_" + y + ".png"
    fig_path = Path(results_dir, fig_name)
    plt.savefig(fig_path)
    plt.close(fig)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
