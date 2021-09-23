from durations import Duration
from sklearn.model_selection import ParameterGrid
from typing import Any, Optional

from timeeval import Algorithm, TrainingType, InputDimensionality
from timeeval.adapters import DockerAdapter

import numpy as np


from timeeval.utils.window import ReverseWindowing
# post-processing for Donut
def post_donut(scores: np.ndarray, args: dict) -> np.ndarray:
    window_size = args.get("hyper_params", {}).get("window_size", 120)
    return ReverseWindowing(window_size=window_size).fit_transform(scores)


_donut_parameters = {
 "epochs": {
  "defaultValue": 256,
  "description": "Number of training passes over entire dataset",
  "name": "epochs",
  "type": "int"
 },
 "latent_size": {
  "defaultValue": 5,
  "description": "Dimensionality of encoding",
  "name": "latent_size",
  "type": "int"
 },
 "linear_hidden_size": {
  "defaultValue": 100,
  "description": "Size of linear hidden layer",
  "name": "linear_hidden_size",
  "type": "int"
 },
 "random_state": {
  "defaultValue": 42,
  "description": "Seed for random number generation.",
  "name": "random_state",
  "type": "int"
 },
 "regularization": {
  "defaultValue": 0.001,
  "description": "Factor for regularization in loss",
  "name": "regularization",
  "type": "float"
 },
 "window_size": {
  "defaultValue": 120,
  "description": "Size of sliding windows",
  "name": "window_size",
  "type": "int"
 }
}


def donut(params: Any = None, skip_pull: bool = False, timeout: Optional[Duration] = None) -> Algorithm:
    return Algorithm(
        name="Donut",
        main=DockerAdapter(
            image_name="mut:5000/akita/donut",
            skip_pull=skip_pull,
            timeout=timeout,
            group_privileges="akita",
        ),
        preprocess=None,
        postprocess=post_donut,
        params=_donut_parameters,
        param_grid=ParameterGrid(params or {}),
        data_as_file=True,
        training_type=TrainingType.SEMI_SUPERVISED,
        input_dimensionality=InputDimensionality("univariate")
    )