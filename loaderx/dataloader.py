import threading
import numpy as np
from queue import Queue

class DataLoader:
    def __init__(self, dataset, labelset, num_workers=4, batch_size=256, prefetch_size=4, shuffle=True, seed=42, transform=(lambda x: x)):
        """
        Initialize a DataLoader.

        Args:
            dataset (BaseDataset): The dataset to load from.
            labelset (BaseDataset): The labelset to load from.
            batch_size (int, optional): The batch size to use. Defaults to 256.
            prefetch_size (int, optional): The number of batches to prefetch. Defaults to 8.
            shuffle (bool, optional): Whether to shuffle the samples. Defaults to True.
            seed (int, optional): The seed to use for shuffling. Defaults to 42.
            transform (callable, optional): A function to apply to the data and label. Defaults to lambda x: x.

        Raises:
            ValueError: If the dataset and labelset have different lengths.
        """
        self.dataset = dataset
        self.labelset = labelset
        if len(dataset) != len(labelset):
            raise ValueError("dataset and labelset must have the same length")

        self.rng = np.random.default_rng(seed)

        self.indices = Queue(maxsize=prefetch_size)
        self.rawes = Queue(maxsize=prefetch_size)
        self.batches = Queue(maxsize=prefetch_size)
        
        self.stop_signal = threading.Event()

        self.threads = [
            threading.Thread(target=self._sampler, args=(batch_size, shuffle, )),
            *[threading.Thread(target=self._fetch) for _ in range(num_workers)],
            *[threading.Thread(target=self._transform, args=(transform, )) for _ in range(num_workers)]
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
                indices = self.rng.choice(n, batch_size, replace=False)
            else:
                indices = (base + pos) % n
                pos = (pos + batch_size) % n
                
            self.indices.put(indices)

    def _fetch(self):
        """
        Fetch the data and label from the dataset and labelset based on the indices
        in the index queue and put them into the raw queue.

        This method is run in a separate thread and is responsible for
        fetching the data and label from the dataset and labelset based on
        the indices in the index queue, and putting the fetched data and
        label into the raw queue.

        The method will stop when the stop signal is set.
        """
        while not self.stop_signal.is_set():
            idxs = self.indices.get()
            self.rawes.put((self.dataset.__getitems__(idxs), self.labelset.__getitems__(idxs)))

    def _transform(self, transform):

        """
        Apply a transformation to the data and label in the raw queue.

        This method is run in a separate thread and is responsible for
        applying a transformation to the data and label in the raw queue,
        and putting the transformed data and label into the batch queue.

        The method will stop when the stop signal is set.

        Args:
            transform (callable): A function that takes data and label as input
                and returns transformed data and label.
        """
        while not self.stop_signal.is_set():
            data, label = transform(self.rawes.get())
            self.batches.put({'data': data, 'label': label})

    def __next__(self):
        """
        Get the next batch from the data loader.

        Returns:
            dict: A dictionary containing the batch data and label.
        """
        # debug: monitor bottlenecks
        # print(self.indices.qsize(), self.rawes.qsize(), self.batches.qsize())
        return self.batches.get()
    
    def __len__(self):
        """
        Raises a TypeError since an external loader has no length.
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
        
        self.dataset.close()
        self.labelset.close()

    def __del__(self):
        """
        Clean up the data loader by stopping all the threads and emptying the queues.
        """
        self.close()