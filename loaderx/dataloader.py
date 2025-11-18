import numpy as np
import threading
from queue import Queue

class DataLoader:
    def __init__(self, dataset, strides,batch_size=256, prefetch_size=8, shuffle=True, seed=42, transform=(lambda x: x)):
        """
        Args:
            dataset (Dataset): dataset to load samples from.
            batch_size (int, optional): batch size. Defaults to 256.
            prefetch (int, optional): number of batches to prefetch. Defaults to 8.
            shuffle (bool, optional): whether to shuffle samples. Defaults to True.
            seed (int, optional): random seed. Defaults to None.
            transform (callable, optional): data transformation function. Defaults to lambda x: x.
        """
        self.dataset = dataset
        self.strides = strides
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        self.step = 0

        self.indices = Queue(maxsize=prefetch_size)
        self.batches = Queue(maxsize=prefetch_size)
        
        self.stop_signal = threading.Event()
        self.lock = threading.Lock()

        self.threads = [
            threading.Thread(target=self._sampler, args=(batch_size, shuffle, )),
            threading.Thread(target=self._prefetch_data, args=(transform, ))
        ]

        for thread in self.threads:
            thread.daemon = True
            thread.start()

    def _sampler(self, batch_size, shuffle):
        pos = 0
        n = len(self.dataset)
        base = np.arange(batch_size)
        
        while not self.stop_signal.is_set():
            if shuffle:
                with self.lock:
                    rng = self.rng
                self.indices.put(rng.choice(n, batch_size, replace=False))
            else:
                batch_idx = (base + pos) % n
                pos = (pos + batch_size) % n
                self.indices.put(batch_idx)

    def _prefetch_data(self, transform):
        while not self.stop_signal.is_set():
            idxs = self.indices.get()
            data, label = transform(self.dataset[idxs])
            self.batches.put(self.batches.put({'data': data, 'label': label}))

    def __next__(self):
        self.step += 1
        if self.step % self.strides == 0:
            self.seed += 1
            with self.lock:
                self.rng = np.random.default_rng(self.seed)
        return self.batches.get()
    
    def __len__(self):
        raise TypeError("Eternal loader has no length.")

    def __iter__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

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

    def __del__(self):
        self.close()