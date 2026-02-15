import threading
import numpy as np
from queue import Queue

from ._sampler import Sampler

class DataLoader:
    def __init__(self, dataset, labelset, num_workers=4, batch_size=256, prefetch_size=4, mode=1, seed=42, transform=(lambda x: x)):
        """
        Initialize a DataLoader.

        Args:
            dataset (BaseDataset): The dataset to load from.
            labelset (BaseDataset): The labelset to load from.
            batch_size (int, optional): The batch size to use. Defaults to 256.
            prefetch_size (int, optional): The number of batches to prefetch. Defaults to 8.
            mode (int, optional): 
            seed (int, optional): The seed to use for shuffling. Defaults to 42.
            transform (callable, optional): A function to apply to the data and label. Defaults to lambda x: x.

        Raises:
            ValueError: If the dataset and labelset have different lengths.
        """
        self.dataset = dataset
        self.labelset = labelset
        if len(dataset) != len(labelset):
            raise ValueError("dataset and labelset must have the same length")

        self.indices = Queue(maxsize=prefetch_size)
        self.batches = Queue(maxsize=prefetch_size)

        self.sampler = Sampler(len(dataset), batch_size, mode, seed)
        
        self.stop_signal = threading.Event()

        self.threads = [
            threading.Thread(target=self._sampler),
            *[threading.Thread(target=self._prefetch, args=(transform, )) for _ in range(num_workers)]
        ]

        for thread in self.threads:
            thread.daemon = True
            thread.start()

    def _sampler(self):
        """
        Sample indices from the dataset and put them into the index queue.
        """
        while not self.stop_signal.is_set():
            self.sampler.next()
            self.indices.put(self.sampler.indices.copy())

    def _prefetch(self, transform):
        """
        Fetch the data and label from the dataset and labelset based on the indices
        in the index queue and put them into the batches queue.
        """
        while not self.stop_signal.is_set():
            idxs = self.indices.get()
            data, label = transform((self.dataset.__getitems__(idxs), self.labelset.__getitems__(idxs)))
            self.batches.put({'data': data, 'label': label})

    def __len__(self):
        """
        Raises a TypeError since an external loader has no length.
        """
        raise TypeError("Eternal loader has no length.")
    
    # iterator
    def __iter__(self):
        return self
    def __next__(self):
        # debug: monitor bottlenecks
        # print(self.indices.qsize(), self.batches.qsize())
        return self.batches.get()
    
    # statement
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # close
    def close(self):
        self.stop_signal.set()
        
        for queue in [self.indices, self.batches]:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except:
                    break
        
        for thread in self.threads:
            thread.join()
        
        self.dataset.close()
        self.labelset.close()

    def __del__(self):
        self.close()