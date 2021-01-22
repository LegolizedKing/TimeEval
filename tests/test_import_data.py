import unittest
import numpy as np
import pandas as pd
from typing import Callable
from pathlib import Path

from timeeval import TimeEval, Algorithm, Datasets


def generates_results(dataset) -> pd.DataFrame:
    datasets_config = Path("./tests/example_data/datasets.json")

    def deviating_from(fn: Callable) -> Callable[[np.ndarray], np.ndarray]:
        def call(data: np.ndarray) -> np.ndarray:
            diffs = np.abs((data - fn(data)))
            diffs = diffs / diffs.max()

            return diffs
        return call

    algorithms = [
        Algorithm(name="deviating_from_mean", main=deviating_from(np.mean)),
        Algorithm(name="deviating_from_median", main=deviating_from(np.median))
    ]

    datasets = Datasets("./tests/example_data", custom_datasets_file=datasets_config)
    timeeval = TimeEval(datasets, [dataset], algorithms)
    timeeval.run()
    return timeeval.results


def generates_results_multi(dataset) -> pd.DataFrame:
    datasets_config = Path("./tests/example_data/datasets.json")

    def deviating_from(fn: Callable) -> Callable[[np.ndarray], np.ndarray]:
        def call(data: np.ndarray) -> np.ndarray:
            diffs = np.abs((data - fn(data, axis=0)))
            diffs = diffs / diffs.max(axis=0)

            return diffs.mean(axis=1)
        return call

    algorithms = [
        Algorithm(name="deviating_from_mean", main=deviating_from(np.mean), data_as_file=False),
        Algorithm(name="deviating_from_median", main=deviating_from(np.median), data_as_file=False)
    ]

    datasets = Datasets("./tests/example_data", custom_datasets_file=datasets_config)
    timeeval = TimeEval(datasets, [dataset], algorithms)
    timeeval.run()
    return timeeval.results


class TestImportData(unittest.TestCase):
    def setUp(self) -> None:
        #  We only compare the columns "algorithm", "collection", "dataset", "score"
        #  without the time measurements, status and error messages
        #  (columns: "preprocessing_time", "main_time", "postprocessing_time", "status", "error_messages").
        self.results = pd.read_csv("./tests/example_data/results.csv")
        self.multi_results = pd.read_csv("./tests/example_data/results_multi.csv")

    def test_generates_correct_results(self):
        DATASET = ("custom", "dataset.1")
        generated_results = generates_results(DATASET)
        true_results = self.results[self.results.dataset == DATASET[1]]

        np.testing.assert_array_equal(generated_results.iloc[:, :4].values, true_results.iloc[:, :4].values)

    def test_generates_correct_results_from_multi_file(self):
        DATASET = ("custom", "dataset.4")
        generated_results = generates_results_multi(DATASET)
        true_results = self.multi_results[self.multi_results.dataset == DATASET[1]]

        np.testing.assert_array_equal(generated_results.iloc[:, :4].values, true_results.iloc[:, :4].values)


if __name__ == "__main__":
    unittest.main()
