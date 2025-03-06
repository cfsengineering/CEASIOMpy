# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import matplotlib as plt
import pandas as pd
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split
import numpy as np
from skopt.space import Real, Categorical
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import SMTRAIN_SM_XPATH
from cpacspy.cpacsfunctions import get_value_or_default, create_branch, add_value
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS
from ceasiompy.SMTrain.func.surrogate import Kriging, MF_Kriging, make_predictions

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def extract_data_set(dataset_paths, objective_coefficient, result_dir):
    """
    Load datasets from the given paths, extract input and selected output columns,
    remove constant input columns, and return them as numpy arrays for multifidelity Kriging.

    param dataset_paths: Dictionary containing dataset file paths.
    param objective_coefficient: String indicating the output variable to extract
    ('CL', 'CD', or 'CM').
    return: Extracted data for available fidelity levels.
    """
    input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]
    datasets = {}

    for level, path in dataset_paths.items():
        if path != "-":

            filename = os.path.basename(path)
            output_file_path = os.path.join(result_dir, filename)

            df = pd.read_csv(path)

            # Check for missing input columns
            missing_inputs = [col for col in input_columns if col not in df.columns]
            if missing_inputs:
                raise KeyError(f"Missing input columns in {level}: {missing_inputs}")

            # Check if objective_coefficient exists in dataset
            if objective_coefficient not in df.columns:
                raise KeyError(
                    f"Objective coefficient '{objective_coefficient}' not found in {level}"
                )

            # Remove constant input columns
            columns_to_keep = [col for col in input_columns if df[col].nunique() > 1]
            removed_columns = list(set(input_columns) - set(columns_to_keep))

            if removed_columns:
                print(f"Removing constant columns in {level}: {removed_columns}")
                df = df[columns_to_keep + [objective_coefficient]]  # Keep only relevant columns
                df.to_csv(output_file_path, index=False)  # Save the modified dataset

            # Extract inputs and outputs
            X = df[columns_to_keep].values
            y = df[objective_coefficient].values
            datasets[level] = (X, y, df)
            print(f"x:{X}")
            print(f"y:{y}")
            print(f"df:{df}")

    return datasets, columns_to_keep


def split_data(datasets, data_repartition, random_state=42):
    """Divide the data into training, validation, and testing sets using only
    the highest fidelity level dataset."""

    # Find the dataset with the highest fidelity level (last in the dictionary)
    highest_fidelity_level = list(datasets.keys())[-1]
    log.info(f"Highest fidelity level dataset: {highest_fidelity_level}")

    # Extract X and y from the highest fidelity level dataset
    X = datasets[highest_fidelity_level][0]  # Inputs
    y = datasets[highest_fidelity_level][1]  # Outputs (e.g., CL)

    log.info(f"Original X shape: {X.shape}, y shape: {y.shape}")
    log.info(f"Original X content: {X}")
    log.info(f"Original y content: {y}")

    # Split into train and test/validation
    X_train, X_t, y_train, y_t = train_test_split(
        X, y, test_size=data_repartition, random_state=random_state
    )

    log.info(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    log.info(f"X_train content: {X_train}")
    log.info(f"y_train content: {y_train}")

    log.info(f"X_t shape: {X_t.shape}, y_t shape: {y_t.shape}")
    log.info(f"X_t content: {X_t}")
    log.info(f"y_t content: {y_t}")

    # Split into validation and test
    X_val, X_test, y_val, y_test = train_test_split(
        X_t, y_t, test_size=0.5, random_state=random_state
    )

    log.info(f"X_val shape: {X_val.shape}, y_val shape: {y_val.shape}")
    log.info(f"X_val content: {X_val}")
    log.info(f"y_val content: {y_val}")

    log.info(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
    log.info(f"X_test content: {X_test}")
    log.info(f"y_test content: {y_test}")

    return X, y, X_train, X_test, X_val, y_train, y_test, y_val


def train_surrogate_model(
    fidelity_level, datasets, X_train, X_test, X_val, y_train, y_test, y_val
):

    # hyperparam_space = [
    #     Real(0.0001, 10, name="theta0"),  # Theta0 (continuo)
    #     Categorical(
    #         ["abs_exp", "squar_exp", "matern52", "matern32"], name="corr"
    #     ),  # Tipo di correlazione
    #     Categorical(["constant", "linear", "quadratic"], name="poly"),  # Tipo di regressione
    #     Categorical(["Cobyla", "TNC"], name="opt"),
    #     Real(1e-12, 1e-1, name="nugget"),
    #     Categorical(["constant", "linear", "quadratic"], name="rho_regr"),
    #     Real(0.1, 1, name="lambda_penalty"),
    # ]

    hyperparam_space = [
        Real(0.2, 0.21, name="theta0"),  # Theta0 (continuo)
        Categorical(["abs_exp"], name="corr"),  # Tipo di correlazione
        Categorical(["constant"], name="poly"),  # Tipo di regressione
        Categorical(["Cobyla"], name="opt"),
        Real(1e-12, 1e-11, name="nugget"),
        Categorical(["constant"], name="rho_regr"),
        Real(0.1, 0.11, name="lambda_penalty"),
    ]

    if fidelity_level == 1:
        model = Kriging(hyperparam_space, X_train, X_test, X_val, y_train, y_test, y_val)

    else:
        model = MF_Kriging(
            fidelity_level,
            datasets,
            hyperparam_space,
            X_train,
            X_test,
            X_val,
            y_train,
            y_test,
            y_val,
        )

    return model


def save_model(model, cpacs_path, cpacs_out_path, result_dir):

    cpacs = CPACS(cpacs_path)

    model_name = "surrogateModel.pkl"
    model_path = os.path.join(result_dir, model_name)

    create_branch(cpacs.tixi, SMTRAIN_SM_XPATH)
    add_value(cpacs.tixi, SMTRAIN_SM_XPATH, model_path)

    with open(model_path, "wb") as file:
        pickle.dump(model, file)

    print(f"model path:{model_path}")

    log.info(f"Model saved to {model_path}")
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


def plot_validation(model, X_test, y_test, label):
    """Crea un grafico Predicted vs Actual"""

    predictions, _ = make_predictions(model, X_test, y_test)

    plt.figure(figsize=(6, 6))
    plt.scatter(y_test, predictions, color="blue", alpha=0.5)
    plt.plot(
        [y_test.min(), y_test.max()],
        [y_test.min(), y_test.max()],
        "r--",
        lw=2,
    )
    plt.title(f"Predicted vs Actual {label}")
    plt.xlabel(f"Actual {label}")
    plt.ylabel(f"Predicted {label}")
    plt.grid()
    plt.show()


def new_doe(datasets, model, columns_to_keep, fraction_of_new_samples, result_dir):

    highest_fidelity_level = list(datasets.keys())[-1]
    log.info(f"Highest fidelity level dataset: {highest_fidelity_level}")

    X, _, df = datasets[highest_fidelity_level]

    _, y_var = make_predictions(model, X)

    y_var_flat = y_var.flatten()
    sorted_indices = np.argsort(y_var_flat)[::-1]
    n_new_samples = len(X) // fraction_of_new_samples
    top_n_indices = sorted_indices[:n_new_samples]
    top_X = X[top_n_indices]

    new_df = pd.DataFrame(top_X, columns=columns_to_keep)

    filename = "suggested_points.csv"
    output_file_path = os.path.join(result_dir, filename)
    new_df.to_csv(output_file_path, index=False)


# def response_surface(model,
#     x_rs,
#     x_rs_ll,
#     x_rs_hl,
#     y_rs,
#     y_rs_ll,
#     y_rs_hl,
#     const_var,
#     fidelity_level,
#     datasets,
# ):

#     # X_lf, y_lf, _ = datasets["first_dataset_path"]
#     # if fidelity_level >= 2:
#     #     X_mf, y_mf, _ = datasets["second_dataset_path"]
#     # if fidelity_level >= 3:
#     #     X_hf, y_hf, _ = datasets["second_dataset_path"]

#     # Find the dataset with the highest fidelity level (last in the dictionary)
#     highest_fidelity_level = list(datasets.keys())[-1]
#     log.info(f"Highest fidelity level dataset: {highest_fidelity_level}")

#     # Extract X and y from the highest fidelity level dataset
#     X, coeff, df = datasets[highest_fidelity_level]

#     input_cols = df.columns[:-1]
#     if x_rs not in input_cols or y_rs not in input_cols:
#         log.warning("")

#     x_grid = np.linspace(x_rs_ll, x_rs_hl, 50)
#     y_grid = np.linspace(y_rs_ll, y_rs_hl, 50)
#     X, Y = np.meshgrid(x_grid, y_grid)  # 2D grid

#     input_data = pd.DataFrame(columns=input_cols)
#     input_data[x_rs] = X.ravel()
#     input_data[y_rs] = Y.ravel()

#     for var in input_cols:
#         if var not in [x_rs, y_rs]:
#             input_data[var] = const_var.get(var)
#         else:
#             input_data[var] = df[var].mean()

#     pred_values = make_predictions(model, input_data.to_numpy())
#     Z = pred_values.reshape(X.shape)

# fig = plt.figure(figsize=(12, 8))
# ax = fig.add_subplot(111, projection="3d")

# ax.plot_trisurf(x, y, z, cmap="viridis", alpha=0.5, edgecolor="none")
# ax.set_xlabel(f"{x_rs}")
# ax.set_ylabel(f"{y_rs}")
# ax.set_zlabel("Predictions")
# ax.set_title(f"Response Surface")
# ax.view_init(elev=25, azim=45)
# ax.legend()

# colorbar = plt.colorbar(ax.collections[0], ax=ax, shrink=0.5, aspect=10)
# colorbar.set_label("Predictions")

# plt.show()


# aeromap (x workflow)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
