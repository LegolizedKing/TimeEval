# DO NOT EDIT THIS FILE!
# This file was automatically generated using the timeeval_experiments.generator from the template:
# timeeval_experiments/generator/templates/docker-algorithm.py.jinja
from durations import Duration
from typing import Any, Dict, Optional

from timeeval import Algorithm, TrainingType, InputDimensionality
from timeeval.adapters import DockerAdapter
from timeeval.params import ParameterConfig

import numpy as np


from timeeval.utils.window import ReverseWindowing
# post-processing for DeepAnT
def _post_deepant(scores: np.ndarray, args: dict) -> np.ndarray:
    window_size = args.get("hyper_params", {}).get("window_size", 45)
    prediction_window_size = args.get("hyper_params", {}).get("prediction_window_size", 1)
    size = window_size + prediction_window_size
    return ReverseWindowing(window_size=size).fit_transform(scores)


_deepant_parameters: Dict[str, Dict[str, Any]] = {
 "batch_size": {
  "defaultValue": 45,
  "description": "Batch size for input data",
  "name": "batch_size",
  "type": "int"
 },
 "early_stopping_delta": {
  "defaultValue": 0.05,
  "description": "If 1 - (loss / last_loss) is less than `delta` for `patience` epochs, stop",
  "name": "early_stopping_delta",
  "type": "float"
 },
 "early_stopping_patience": {
  "defaultValue": 10,
  "description": "If 1 - (loss / last_loss) is less than `delta` for `patience` epochs, stop",
  "name": "early_stopping_patience",
  "type": "int"
 },
 "epochs": {
  "defaultValue": 50,
  "description": "Number of training epochs",
  "name": "epochs",
  "type": "int"
 },
 "learning_rate": {
  "defaultValue": 1e-05,
  "description": "Learning rate",
  "name": "learning_rate",
  "type": "float"
 },
 "prediction_window_size": {
  "defaultValue": 1,
  "description": "Prediction window: Number of data points that will be predicted from each window",
  "name": "prediction_window_size",
  "type": "int"
 },
 "random_state": {
  "defaultValue": 42,
  "description": "Seed for the random number generator",
  "name": "random_state",
  "type": "int"
 },
 "split": {
  "defaultValue": 0.8,
  "description": "Train-validation split for early stopping",
  "name": "split",
  "type": "float"
 },
 "window_size": {
  "defaultValue": 45,
  "description": "History window: Number of time stamps in history, which are taken into account",
  "name": "window_size",
  "type": "int"
 }
}


def deepant(params: Optional[ParameterConfig] = None, skip_pull: bool = False, timeout: Optional[Duration] = None) -> Algorithm:
    """DeepAnT

    Adapted community implementation (https://github.com/dev-aadarsh/DeepAnT)


    **Algorithm Parameters:**

    epochs: int
        Number of training epochs (default: ``50``)
    window_size: int
        History window: Number of time stamps in history, which are taken into account (default: ``45``)
    prediction_window_size: int
        Prediction window: Number of data points that will be predicted from each window (default: ``1``)
    learning_rate: float
        Learning rate (default: ``1e-05``)
    batch_size: int
        Batch size for input data (default: ``45``)
    random_state: int
        Seed for the random number generator (default: ``42``)
    split: float
        Train-validation split for early stopping (default: ``0.8``)
    early_stopping_delta: float
        If 1 - (loss / last_loss) is less than `delta` for `patience` epochs, stop (default: ``0.05``)
    early_stopping_patience: int
        If 1 - (loss / last_loss) is less than `delta` for `patience` epochs, stop (default: ``10``)

    Parameters
    ----------
    params : Optional[ParameterConfig]
        Parameter configuration for the algorithm
    skip_pull : bool
        Set to ``True`` to skip pulling the Docker image and use a local image instead.
        If the image is not present locally, this will raise an error.
    timeout : Optional[Duration]
        Set an individual execution and training timeout for this algorithm.
        This will overwrite the global timeouts set using :class:`~timeeval.ResourceConstraints`.

    Returns
    -------
    ~timeeval.Algorithm
        A correctly configured :class:`~timeeval.Algorithm` object for the DeepAnT algorithm.
    """
    return Algorithm(
        name="DeepAnT",
        main=DockerAdapter(
            image_name="ghcr.io/timeeval/deepant",
            tag="0.3.0",
            skip_pull=skip_pull,
            timeout=timeout,
            group_privileges="akita",
        ),
        preprocess=None,
        postprocess=_post_deepant,
        param_schema=_deepant_parameters,
        param_config=params or ParameterConfig.defaults(),
        data_as_file=True,
        training_type=TrainingType.SEMI_SUPERVISED,
        input_dimensionality=InputDimensionality("multivariate")
    )