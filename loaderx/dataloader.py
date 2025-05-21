import numpy as np
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

class DataLoader:
    def __init__(self, dataset, batch_size=256, shuffle=True, prefetch=2, num_epoch=1, seed=None):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.prefetch = prefetch
        self.num_epoch = num_epoch
        self.seed = seed

        self.indices = list(range(len(dataset)))
        self.queue = Queue(maxsize=prefetch)
        self.stop_signal = threading.Event()
        self.current_epoch = 0

        self.thread = threading.Thread(target=self._prefetch_data)
        self.thread.start()

    def _prefetch_data(self):
        while not self.stop_signal.is_set() and self.current_epoch < self.num_epoch:
            if self.shuffle:
                if self.seed is not None:
                    np.random.seed(self.seed + self.current_epoch)
                np.random.shuffle(self.indices)
            for i in range(0, len(self.indices), self.batch_size):
                batch_indices = self.indices[i:i + self.batch_size]         
                with ThreadPoolExecutor() as executor:
                    batch = executor.map(self.dataset.__getitem__, batch_indices)
                batch_data, batch_labels = zip(*batch)
                self.queue.put({'data': np.stack(batch_data), 'label': np.stack(batch_labels)})
            self.current_epoch += 1
        self.stop_signal.set()

    def __iter__(self):
        return self

    def __next__(self):
        if self.stop_signal.is_set() and self.queue.empty():
            raise StopIteration
        return self.queue.get()

    def __del__(self):
        try:
            self.stop_signal.set()
            if hasattr(self, 'thread') and self.thread is not None and self.thread.is_alive():
                self.thread.join()
        except Exception:
            pass