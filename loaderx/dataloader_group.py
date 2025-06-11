import numpy as np
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

"""
group_size [4,32]
"""
class DataLoader_Group:
    def __init__(self, dataset, batch_size=256, group_size=16, num_epochs=1, prefetch=2, shuffle=True, seed=None, num_workers=8, backend="threading"):
        self.dataset = dataset
        self.batch_size = batch_size
        self.group_size = group_size
        self.batch_groups = batch_size // group_size
        self.num_groups = len(dataset)

        self.shuffle = shuffle
        self.seed = seed

        self.num_workers = num_workers
        self.backend = backend

        self.indices = list(range(self.num_groups))
        self.num_epochs = num_epochs
        self.queue = Queue(maxsize=prefetch)
        
        self.stop_signal = threading.Event()
        self.current_epoch = 0
        self.thread = threading.Thread(target=self._prefetch_data)
        self.thread.start()

    def _prefetch_data(self):
        while not self.stop_signal.is_set() and self.current_epoch < self.num_epochs:
            if self.shuffle:
                if self.seed is not None:
                    np.random.seed(self.seed + self.current_epoch)
                np.random.shuffle(self.indices)
            for i in range(0, self.num_groups, self.batch_groups):
                indices = self.indices[i:i + self.batch_groups]
                with ThreadPoolExecutor() as executor:
                    batch = list(executor.map(self.dataset.__getgroup__, indices))
                data, label = zip(*batch)
                self.queue.put({'data': np.concatenate(data, axis=0), 'label': np.concatenate(label, axis=0)})
            self.current_epoch += 1
        self.stop_signal.set()

    def __iter__(self):
        return self

    def __next__(self):
        if self.stop_signal.is_set() and self.queue.empty():
            raise StopIteration
        return self.queue.get()

    def __len__(self):
        return np.ceil(self.num_groups / self.batch_groups).astype(int) * self.num_epochs

    def __del__(self):
        try:
            self.stop_signal.set()
            if hasattr(self, 'thread') and self.thread is not None and self.thread.is_alive():
                self.thread.join()
        except Exception:
            pass
