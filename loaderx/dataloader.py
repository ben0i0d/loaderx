import numpy as np
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

class DataLoader:
    def __init__(self, dataset, batch_size=256, num_epochs=1, prefetch=2, shuffle=True, seed=None, num_workers=8, backend="threading"):
        self.dataset = dataset
        self.batch_size = batch_size
        self.num_epochs = num_epochs

        self.shuffle = shuffle
        self.seed = seed
        
        self.num_workers = num_workers
        self.backend = backend
        
        self.indices = list(range(len(dataset)))
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
            for i in range(0, len(self.indices), self.batch_size):
                indices = self.indices[i:i + self.batch_size]         
                with ThreadPoolExecutor() as executor:
                    batch = executor.map(self.dataset.__getitem__, indices)
                data, label = zip(*batch)
                self.queue.put({'data': np.stack(data), 'label': np.stack(label)})
            self.current_epoch += 1
        self.stop_signal.set()

    def __iter__(self):
        return self

    def __next__(self):
        if self.stop_signal.is_set() and self.queue.empty():
            raise StopIteration
        return self.queue.get()
    
    def __len__(self):
        return np.ceil(len(self.dataset) / self.batch_size).astype(int) * self.num_epochs

    def __del__(self):
        try:
            self.stop_signal.set()
            if hasattr(self, 'thread') and self.thread is not None and self.thread.is_alive():
                self.thread.join()
        except Exception:
            pass