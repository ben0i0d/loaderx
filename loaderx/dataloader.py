import numpy as np
import threading
from queue import Queue

class DataLoader:
    def __init__(self, dataset, batch_size=256, num_epochs=1, prefetch=4, shuffle=True, seed=None, transform=None, monitor=False):
        """
        Args:
            dataset (Dataset): The dataset to load data from.
            batch_size (int): Number of samples per batch.
            num_epochs (int): Number of epochs to iterate over the dataset.
            prefetch (int): Number of batches to prefetch in the background.
            shuffle (bool): Whether to shuffle the dataset at the beginning of each epoch.
            seed (int, optional): Random seed for shuffling.
            transform (callable, optional): A function to apply transformations to the batch.
                batch = (data, label)
                transform should return a tuple of (data, label) after transformation
                Example:
                def transform(batch):
                    return batch[0][..., None] / 255.0 , batch[1].astype(numpy.int32)
            monitor (bool): If True, will print queue size to monitor any I/O bottlenecks.
        
        """
        self.dataset = dataset
        self.batch_size = batch_size
        
        self.batch_groups = batch_size // self.dataset.group_size
        self.num_groups = self.dataset.num_groups

        self.shuffle = shuffle
        self.seed = seed

        self.transform = transform or (lambda x: x)
        self.monitor = monitor

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
                data, label = self.transform(self.dataset[indices])
                self.queue.put({'data': data, 'label': label})
            self.current_epoch += 1
        self.stop_signal.set()

    def __iter__(self):
        return self

    def __next__(self):
        if self.stop_signal.is_set() and self.queue.empty():
            raise StopIteration
        
        if self.monitor:
            self._monitor_counter = getattr(self, '_monitor_counter', 0) + 1
            if self._monitor_counter % 100 == 0 and self.queue.qsize() < self.queue.maxsize:
                print(f"[WARN] Queue not full ({self.queue.qsize()}/{self.queue.maxsize}) — potential I/O bottleneck detected.")

        return self.queue.get()
    
    def __len__(self):
        return -(-len(self.dataset) // self.batch_size) * self.num_epochs

    def __del__(self):
        try:
            self.stop_signal.set()
            if hasattr(self, 'thread') and self.thread is not None and self.thread.is_alive():
                self.thread.join()
        except Exception:
            pass