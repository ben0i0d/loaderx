import numpy as np

class Dataset:
    def __init__(self, dataset_path, data, label, group_size=1):
        """
        Initialize dataset, override in subclass if needed.
        Args:
            dataset_path (str): Path to the dataset file.
            data (str): Key for the data array in the dataset file.
            label (str): Key for the label array in the dataset file.
            group_size (int): Number of samples to group together. Default is 1.(per-sample sampling)
        """
        self._data = np.load(dataset_path)[data]
        self._label = np.load(dataset_path)[label]
        
        self.group_size = group_size
        self.num_groups = -(-len(self._data) // self.group_size)
        
        if len(self._data) % self.group_size != 0:
          self.__pad__()

    def __pad__(self):
        """
        Pad the dataset to ensure it has a multiple of group_size samples.
        """
        pad_len = self.group_size * self.num_groups - len(self._data)
        if pad_len > 0:
            indices = np.random.choice(len(self._data), pad_len, replace=True)
            self._data = np.concatenate([self._data, self._data[indices]], axis=0)
            self._label = np.concatenate([self._label, self._label[indices]], axis=0)

    def __getitem__(self, idxs):
        """
        Retrieve a list of grouped data samples by their start indices.

        Args:
            idxs (List[int]): List of starting indices for groups.

        Returns:
            Tuple[np.ndarray, np.ndarray]:
                Two ndarray, each containing group_size-sized chunks of data and labels
                corresponding to each start index in idxs.
        """
        return  np.concatenate([self._data[idx:idx+self.group_size] for idx in idxs], axis=0), \
                np.concatenate([self._label[idx:idx+self.group_size] for idx in idxs], axis=0)

    def __len__(self):
        """
        Returns:
            int: Total number of samples in the dataset (including any padding).
        """
        return len(self._data)
