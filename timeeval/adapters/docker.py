import json
import subprocess
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path, WindowsPath, PosixPath
from typing import Optional, Any, Callable

import docker
import numpy as np
import requests
from docker.models.containers import Container
from durations import Duration

from .base import Adapter, AlgorithmParameter

DATASET_TARGET_PATH = "/data"
RESULTS_TARGET_PATH = "/results"
SCORES_FILE_NAME = "docker-algorithm-scores.csv"
MODEL_FILE_NAME = "model.pkl"

DEFAULT_TIMEOUT = Duration("8 hours")


class DockerJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, ExecutionType):
            return o.name.lower()
        elif isinstance(o, (PosixPath, WindowsPath)):
            return str(o)
        return super().default(o)


class ExecutionType(Enum):
    TRAIN = 0
    EXECUTE = 1


class DockerTimeoutError(BaseException):
    pass


class DockerAlgorithmFailedError(BaseException):
    pass


@dataclass
class AlgorithmInterface:
    dataInput: Path
    dataOutput: Path
    modelInput: Path
    modelOutput: Path
    customParameters: dict = field(default_factory=dict)
    executionType: ExecutionType = ExecutionType.EXECUTE

    def to_json_string(self) -> str:
        dictionary = asdict(self)
        return json.dumps(dictionary, cls=DockerJSONEncoder)


class DockerAdapter(Adapter):
    def __init__(self, image_name: str, tag: str = "latest", group_privileges="akita", skip_pull=False,
                 timeout=DEFAULT_TIMEOUT):
        self.image_name = image_name
        self.tag = tag
        self.group = group_privileges
        self.skip_pull = skip_pull
        self.timeout = timeout

    @staticmethod
    def _get_gid(group: str) -> str:
        CMD = "getent group %s | cut -d ':' -f 3"
        return subprocess.run(CMD % group, capture_output=True, text=True, shell=True).stdout.strip()

    @staticmethod
    def _get_uid() -> str:
        return subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip()

    def _run_container(self, dataset_path: Path, args: dict) -> Container:
        client = docker.from_env()

        algorithm_interface = AlgorithmInterface(
            dataInput=(Path(DATASET_TARGET_PATH) / dataset_path.name).absolute(),
            dataOutput=(Path(RESULTS_TARGET_PATH) / SCORES_FILE_NAME).absolute(),
            modelInput=(Path(RESULTS_TARGET_PATH) / MODEL_FILE_NAME).absolute(),
            modelOutput=(Path(RESULTS_TARGET_PATH) / MODEL_FILE_NAME).absolute(),
            customParameters=args.get("hyper_params", {})
        )

        gid = DockerAdapter._get_gid(self.group)
        uid = DockerAdapter._get_uid()
        print(f"Running container with uid={uid} and gid={gid} privileges")
        return client.containers.run(
            f"{self.image_name}:{self.tag}",
            f"execute-algorithm '{algorithm_interface.to_json_string()}'",
            volumes={
                str(dataset_path.parent.absolute()): {'bind': DATASET_TARGET_PATH, 'mode': 'ro'},
                str(args.get("results_path", Path("./results")).absolute()): {'bind': RESULTS_TARGET_PATH, 'mode': 'rw'}
            },
            environment={
                "LOCAL_GID": gid,
                "LOCAL_UID": uid
            },
            detach=True
        )

    def _run_until_timeout(self, container: Container, args: dict):
        try:
            result = container.wait(timeout=self.timeout.to_seconds())
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            if "timed out" in str(e):
                container.stop()
                raise DockerTimeoutError(f"{self.image_name} timed out after {self.timeout}") from e
            else:
                raise e

        if result["StatusCode"] != 0:
            result_path = str(args.get("results_path", Path("./results")).absolute())
            raise DockerAlgorithmFailedError(f"Please consider log files in {result_path}!")

    def _read_results(self, args: dict) -> np.ndarray:
        return np.loadtxt(args.get("results_path", Path("./results")) / SCORES_FILE_NAME)

    # Adapter overwrites

    def _call(self, dataset: AlgorithmParameter, args: Optional[dict] = None) -> AlgorithmParameter:
        assert isinstance(dataset, (WindowsPath, PosixPath)), \
            "Docker adapters cannot handle NumPy arrays! Please put in the path to the dataset."
        args = args or {}
        container = self._run_container(dataset, args)
        self._run_until_timeout(container, args)

        return self._read_results(args)

    def get_prepare_fn(self) -> Optional[Callable[[], None]]:
        if not self.skip_pull:
            # capture variables for the function closure
            image = self.image_name
            tag = self.tag

            def prepare():
                client = docker.from_env()
                client.images.pull(image, tag=tag)
            return prepare
        else:
            return None

    def get_finalize_fn(self) -> Optional[Callable[[], None]]:
        def finalize():
            client = docker.from_env()
            client.containers.prune()
        return finalize
