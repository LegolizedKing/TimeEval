from distributed.client import Future

import numpy as np
import pandas as pd
from typing import List, Callable, Tuple, Any, NamedTuple, Dict, Union, Optional
import tqdm
from pathlib import Path
import logging
import time

from .remote import Remote
from timeeval.datasets import Datasets
from timeeval.utils.metrics import roc


class Algorithm(NamedTuple):
    name: str
    function: Callable[[Union[np.ndarray, Path]], np.ndarray]
    data_as_file: bool


class Times(NamedTuple):
    pre: Optional[float]
    main: float
    post: Optional[float]

    def to_dict(self) -> Dict:
        return dict(self._asdict())


def timer(fn: Callable, *args, **kwargs) -> Tuple[Any, Times]:
    start = time.time()
    fn_result = fn(*args, **kwargs)
    end = time.time()
    duration = end - start
    return fn_result, Times(pre=None, main=duration, post=None)


class TimeEval:
    def __init__(self,
                 datasets: List[str],
                 algorithms: List[Algorithm],
                 dataset_config: Path,
                 distributed: bool = False,
                 remote_hosts: Optional[List[str]] = None,
                 threads_per_worker: int = 1):
        self.dataset_names = datasets
        self.algorithms = algorithms
        self.dataset_config = dataset_config
        self.distributed = distributed
        self.remote_hosts = remote_hosts
        self.threads_per_worker = threads_per_worker
        self.results = pd.DataFrame(columns=("algorithm", "dataset", "score", "preprocess_time", "main_time", "postprocess_time"))

        if self.distributed:
            self.remote = Remote(self.remote_hosts, self.threads_per_worker)
            self.results["future_result"] = np.nan

    def _load_dataset(self, name) -> pd.DataFrame:
        return Datasets(name).load(self.dataset_config)

    def _get_dataset_path(self, name) -> Tuple[Path, Optional[Path]]:
        return Datasets(name).get_path(self.dataset_config)

    def _run_algorithm(self, algorithm: Algorithm):
        for dataset_name in tqdm.tqdm(self.dataset_names, desc=f"Evaluating {algorithm.name}", position=1):
            if algorithm.data_as_file:
                dataset_file, label_file = self._get_dataset_path(dataset_name)
                self._run_from_data_file(algorithm, dataset_file, label_file, dataset_name)
            else:
                dataset = self._load_dataset(dataset_name)
                self._run_w_loaded_data(algorithm, dataset, dataset_name)

    def _run_from_data_file(self, algorithm: Algorithm, dataset_file: Path, label_file: Optional[Path], dataset_name: str):
        raise NotImplementedError()

    def _run_w_loaded_data(self, algorithm: Algorithm, dataset: pd.DataFrame, dataset_name: str):
        try:
            if self.distributed:
                result = self.remote.add_task(TimeEval.evaluate, algorithm, dataset, dataset_name)
            else:
                result = TimeEval.evaluate(algorithm, dataset, dataset_name)
            self._record_results(algorithm.name, dataset_name, result)

        except Exception as e:
            logging.error(f"Exception occured during the evaluation of {algorithm.name} on the dataset {dataset_name}:")
            logging.error(str(e))

    @staticmethod
    def evaluate(algorithm: Algorithm, dataset: pd.DataFrame, dataset_name: str) -> Dict:
        y_true = dataset.values[:, -1]
        if dataset.shape[1] > 3:
            X = dataset.values[:, 1:-1]
        elif dataset.shape[1] == 3:
            X = dataset.values[:, 1]
        else:
            raise ValueError(f"Dataset '{dataset_name}' has a shape that was not expected: {dataset.shape}")
        y_scores = algorithm.function(X)
        score, times = timer(roc, y_scores, y_true.astype(np.float), plot=False)
        return {
            "score": score,
            "preprocess_time": times.pre,
            "main_time": times.main,
            "postprocess_time": times.post
        }

    def _record_results(self, algorithm_name: str, dataset_name: str, result: Union[Dict, Future]):
        new_row = dict(algorithm=algorithm_name, dataset=dataset_name)
        if type(result) == dict:
            new_row.update(result)
        else:
            new_row.update(dict(future_result=result))
        self.results = self.results.append(new_row, ignore_index=True)

    def _get_future_results(self):
        keys = ["score", "preprocess_time", "main_time", "postprocess_time"]

        def get_future_result(f: Future) -> List[float]:
            r = f.result()
            return [r[k] for k in keys]

        self.remote.fetch_results()
        self.results[keys] = self.results["future_result"].apply(get_future_result).tolist()
        self.results = self.results.drop(['future_result'], axis=1)

    def run(self):
        assert len(self.algorithms) > 0, "No algorithms given for evaluation"

        for algorithm in tqdm.tqdm(self.algorithms, desc="Evaluating Algorithms", position=0):
            self._run_algorithm(algorithm)

        if self.distributed:
            self._get_future_results()
            self.remote.close()
