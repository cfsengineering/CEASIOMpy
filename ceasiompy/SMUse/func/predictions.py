"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================

from smt.utils.misc import compute_rmse

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def make_predictions(datasets, model):
    predictions_dict = {}

    # Iterate through all datasets in the dictionary
    for dataset_name, dataset_content in datasets.items():
        prediction_dataset = dataset_content["df_filtered"]

        # Check if the dataset is empty
        if prediction_dataset.empty:
            log.error(f"{dataset_name} is empty. No predictions can be made.")
            raise ValueError(f"The prediction dataset {dataset_name} is empty.")

        # Convert the dataset into a NumPy array for prediction
        X_pred = prediction_dataset.to_numpy()

        # Make predictions using the trained model
        y_pred = model.predict_values(X_pred)

        # Compute RMSE for the dataset
        rmse = compute_rmse(model, X_pred, y_pred)
        log.info(f"RMSE for {dataset_name}: {rmse}")

        # Store the predictions in the dictionary
        predictions_dict[dataset_name] = {"predictions": y_pred, "rmse": rmse}

    return predictions_dict


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
