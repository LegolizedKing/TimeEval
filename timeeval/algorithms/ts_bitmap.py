# DO NOT EDIT THIS FILE!
# This file was automatically generated using the timeeval_experiments.generator from the template:
# timeeval_experiments/generator/templates/docker-algorithm.py.jinja
from durations import Duration
from typing import Any, Dict, Optional

from timeeval import Algorithm, TrainingType, InputDimensionality
from timeeval.adapters import DockerAdapter
from timeeval.params import ParameterConfig


_ts_bitmap_parameters: Dict[str, Dict[str, Any]] = {
 "alphabet_size": {
  "defaultValue": 5,
  "description": "Number of bins for SAX discretization.",
  "name": "alphabet_size",
  "type": "int"
 },
 "compression_ratio": {
  "defaultValue": 2,
  "description": "How much to compress the timeseries in the PAA step. If `compression_ration == 1`, no compression.",
  "name": "compression_ratio",
  "type": "int"
 },
 "feature_window_size": {
  "defaultValue": 100,
  "description": "Size of the tumbling windows used for SAX discretization.",
  "name": "feature_window_size",
  "type": "int"
 },
 "lag_window_size": {
  "defaultValue": 300,
  "description": "How far to look back to create the lag bitmap.",
  "name": "lag_window_size",
  "type": "int"
 },
 "lead_window_size": {
  "defaultValue": 200,
  "description": "How far to look ahead to create lead bitmap.",
  "name": "lead_window_size",
  "type": "int"
 },
 "level_size": {
  "defaultValue": 3,
  "description": "Desired level of recursion of the bitmap.",
  "name": "level_size",
  "type": "int"
 },
 "random_state": {
  "defaultValue": 42,
  "description": "Seed for random number generation.",
  "name": "random_state",
  "type": "int"
 }
}


def ts_bitmap(params: Optional[ParameterConfig] = None, skip_pull: bool = False, timeout: Optional[Duration] = None) -> Algorithm:
    """TSBitmap

    Implementation of https://dl.acm.org/doi/abs/10.5555/1116877.1116907


    **Algorithm Parameters:**

    feature_window_size: int
        Size of the tumbling windows used for SAX discretization. (default: ``100``)
    lead_window_size: int
        How far to look ahead to create lead bitmap. (default: ``200``)
    lag_window_size: int
        How far to look back to create the lag bitmap. (default: ``300``)
    alphabet_size: int
        Number of bins for SAX discretization. (default: ``5``)
    level_size: int
        Desired level of recursion of the bitmap. (default: ``3``)
    compression_ratio: int
        How much to compress the timeseries in the PAA step. If `compression_ration == 1`, no compression. (default: ``2``)
    random_state: int
        Seed for random number generation. (default: ``42``)

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
        A correctly configured :class:`~timeeval.Algorithm` object for the TSBitmap algorithm.
    """
    return Algorithm(
        name="TSBitmap",
        main=DockerAdapter(
            image_name="ghcr.io/timeeval/ts_bitmap",
            tag="0.3.0",
            skip_pull=skip_pull,
            timeout=timeout,
            group_privileges="akita",
        ),
        preprocess=None,
        postprocess=None,
        param_schema=_ts_bitmap_parameters,
        param_config=params or ParameterConfig.defaults(),
        data_as_file=True,
        training_type=TrainingType.UNSUPERVISED,
        input_dimensionality=InputDimensionality("univariate")
    )