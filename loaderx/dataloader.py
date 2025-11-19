import numpy as np
import threading
from queue import Queue

class DataLoader:
    def __init__(self, dataset, batch_size=256, prefetch_size=8, shuffle=True, seed=42, transform=(lambda x: x)):
        """
        Initialize DataLoader.

        Args:
            dataset (Dataset): The dataset to load.
            strides (int): The number of samples to load at a time.
            batch_size (int, optional): The batch size. Defaults to 256.
            prefetch_size (int, optional): The number of batches to prefetch. Defaults to 8.
            shuffle (bool, optional): Whether to shuffle the samples. Defaults to True.
            seed (int, optional): The random seed. Defaults to 42.
            transform (callable, optional): A data transformation function. Defaults to (lambda x: x).

        """
        self.dataset = dataset
        self.rng = np.random.default_rng(seed)

        self.step = 0

        self.indices = Queue(maxsize=prefetch_size)
        self.batches = Queue(maxsize=prefetch_size)
        
        self.stop_signal = threading.Event()

        self.threads = [
            threading.Thread(target=self._sampler, args=(batch_size, shuffle, )),
            threading.Thread(target=self._prefetch_data, args=(transform, ))
        ]

        for thread in self.threads:
            thread.daemon = True
            thread.start()

    def _sampler(self, batch_size, shuffle):
        """
        Sample indices from the dataset and put them into the index queue.

        This method is run in a separate thread and is responsible for
        sampling indices from the dataset and putting them into the index
        queue.

        Args:
            batch_size (int): batch size.
            shuffle (bool): whether to shuffle samples.
        """
        pos = 0
        n = len(self.dataset)
        base = np.arange(batch_size)
        
        while not self.stop_signal.is_set():
            if shuffle:
                self.indices.put(self.rng.choice(n, batch_size, replace=False))
            else:
                batch_idx = (base + pos) % n
                pos = (pos + batch_size) % n
                self.indices.put(batch_idx)

    def _prefetch_data(self, transform):
        """
        Prefetch data from the dataset into the batch queue.

        This method is run in a separate thread and is responsible for
        fetching data from the dataset, transforming it, and putting it
        into the batch queue.

        Args:
            transform (callable): data transformation function.
        """
        while not self.stop_signal.is_set():
            idxs = self.indices.get()
            data, label = transform(self.dataset[idxs])
            self.batches.put({'data': data, 'label': label})

    def __next__(self):
        """
        Get the next batch from the data loader.

        Returns:
            dict: A dictionary containing the batch data and label.
        """
        self.step += 1
        return self.batches.get()
    
    def __len__(self):
        """
        Raises a TypeError since an external loader has no length.

        Returns:
            None
        """
        raise TypeError("Eternal loader has no length.")

    def __iter__(self):
        """
        Return an iterator over the data loader.

        Returns:
            DataLoader: self
        """
        return self

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        Returns:
            DataLoader: self
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close the data loader, stopping all the threads and emptying the queues.

        This method is called automatically when the data loader is used in a with statement.
        """
        self.close()

    def close(self):
        """
        Stop all the threads and empty the queues.

        This method is used to manually stop the data loader.
        """
        self.stop_signal.set()
        
        for queue in [self.indices, self.batches]:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except:
                    break
        
        for thread in self.threads:
            thread.join()

    def __del__(self):
        """
        Clean up the data loader by stopping all the threads and emptying the queues.
        """
        self.close()