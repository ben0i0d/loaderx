import numpy as np

class Dataset:
    def __init__(self, data_path, label_path, mmap=True):
        """
        Initialize dataset, override in subclass if needed.
        Args:
            data_path (str): Path to the dataset file.
            label_path (str): Path to the dataset file.
            mmap (bool, optional): Whether to use mmap. Defaults to True.
        """
        mode = 'r' if mmap else None

        self._data = np.load(data_path, mmap_mode=mode)
        self._label = np.load(label_path, mmap_mode=mode)

        if self._data.shape[0] != self._label.shape[0]:
            raise ValueError('data and label must have the same number of samples.')

    def __getitem__(self, idx):
        """
        Get a sample from the dataset by its index.

        Args:
            idx (int): Index of the sample to retrieve.

        Returns:
            dict: A dictionary containing the sample data and label.
        """
        return self._data[idx], self._label[idx]

    def __len__(self):
        """
        Return the number of samples in the dataset.
        Returns:
            int: The number of samples in the dataset.
        """
        return len(self._data)
