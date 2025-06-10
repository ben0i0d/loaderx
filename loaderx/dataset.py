"""
class Dataset:
    def __init__(self, npz_path):
        npz = np.load(npz_path)
        self.data = npz['data']
        self.label = npz['label']

    def __getitem__(self, idx):
        return self.data[idx], self.label[idx]

    def __len__(self):
        return len(self.data)
"""
class Dataset:
    def __init__(self):
        pass

    def __getitem__(self):
        pass

    def __len__(self):
        pass