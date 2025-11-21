import numpy as np
from array_record.python.array_record_data_source import ArrayRecordDataSource

class BaseDataset:
    def __init__(self, path):
        """
        Initialize a dataset.
        """
        raise NotImplementedError
    def __getitem__(self, idx):
        """
        Get the item at index idx from the dataset.

        Args:
            idx (int): Index of the item to retrieve.

        Returns:
            np.ndarray: The item at index idx from the dataset.
        """
        raise NotImplementedError
    def __len__(self):
        """
        Return the number of samples in the dataset.

        Returns:
            int: The number of samples in the dataset.
        """
        raise NotImplementedError
    def __getitems__(self, idxs):
        """
        Get the items at index idxs from the dataset.

        Args:
            idxs (list of int): indices of the items to retrieve.

        Returns:
            np.ndarray: The items at index idxs from the dataset.
        """
        raise NotImplementedError
    def close(self):
        """
        Close the dataset.

        If the dataset is stored in a memory-mapped file,
        close the memory map to free up system resources.

        If the dataset is stored in an ArrayRecord file,
        close the file to free up system resources.
        """
        pass

class NPDataset(BaseDataset):
    def __init__(self, path):
        self._array = np.load(path, mmap_mode='r')

    def __getitem__(self, idx):
        return self._array[idx]

    def __getitems__(self, idxs):
        return self._array[idxs]

    def __len__(self):
        return len(self._array)

    def close(self):
        mmap_obj = getattr(self._array, "_mmap", None)
        if mmap_obj is not None:
            mmap_obj.close()

class ARDataset(BaseDataset):
    def __init__(self, path, dtype=None, shape=None):
        if dtype is None or shape is None:
            raise ValueError("dtype and shape must be specified when backend is ar")
        self._dtype = dtype
        self._shape = shape
        self._array = ArrayRecordDataSource(path)

    def __getitem__(self, idx):
        return np.frombuffer(self._array[idx], dtype=self._dtype).reshape(self._shape)

    def __getitems__(self, idxs):
        return np.frombuffer(b"".join(self._array.__getitems__(idxs)), dtype=self._dtype).reshape(len(idxs), *self._shape)

    def __len__(self):
        return len(self._array)

    def close(self):
        self._array.__exit__(None, None, None)