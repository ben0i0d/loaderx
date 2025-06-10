"""
class Dataset_Group:
    def __init__(self, npz_path, group_size):
        npz = np.load(npz_path)
        self.data = npz['data']
        self.label = npz['label']
        self.group_size = group_size
        self.length = len(self.data)

        self.num_groups = numpy.ceil(len(self.data) / self.group_size)

    def __getgroup__(self, idx):
        # 获取指定组的数据和标签，最后一组可能不足 group_size
        if idx >= self.total_groups:
            raise IndexError("Group index out of range.")
        start = idx * self.group_size
        end = min((idx + 1) * self.group_size, self.length)
        return self.data[start:end], self.label[start:end]

    def __len__(self):
        return self.num_groups
"""
class Dataset_Group:
    def __init__(self):
        pass

    def __getgroup__(self):
        pass

    def __len__(self):
        pass