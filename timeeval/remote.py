from asyncio import Future
from typing import List, Callable, Optional
from dask.distributed import Client, SSHCluster


class Remote:
    def __init__(self, hosts: List[str], threads_per_worker: int = 1):
        self.hosts = hosts
        self.threads_per_worker = threads_per_worker
        self.client: Optional[Client] = None
        self.cluster: Optional[SSHCluster] = None
        self.futures: List[Future] = []

    def _start_cluster(self):
        self.cluster = SSHCluster(hosts=self.hosts, worker_options={"threads": self.threads_per_worker})
        self.client = Client(self.cluster)

    def add_task(self, task: Callable, *args) -> Future:
        if self.cluster is None:
            self._start_cluster()
        future = self.client.submit(task, *args)
        self.futures.append(future)
        return future

    def fetch_results(self):
        self.client.gather(self.futures)

    def close(self):
        self.client.close()
        self.cluster.close()
