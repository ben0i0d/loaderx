# loaderx
A Minimal Data Loader for Flax

## Why Create loaderx?

While Flax supports multiple data-loading backends—including PyTorch, TensorFlow, Grain, and jax_dataloader—each comes with notable drawbacks:

1. Installing large frameworks like PyTorch or TensorFlow *just* for data loading is often undesirable.
2. Grain provides a clean API, but its real-world performance can be suboptimal.
3. jax_dataloader defaults to using GPU memory, which may lead to inefficient memory utilization in some workflows.

## Design Philosophy

loaderx is built around several core principles:

1. A pragmatic approach that prioritizes minimal memory overhead and minimal dependencies.
2. A strong focus on single-machine training workflows.
3. We implement based on NumPy semantics, supporting both NumPy (for small to medium datasets) and ArrayRecord (for large-scale datasets) backends. Please note that when using ArrayRecord for writing, the group_size must be set to 1.
4. An **immortal (endless) step-based data loader**, rather than the traditional epoch-based design—better aligned with modern ML training practices.

## Current Limitations
Currently, loaderx only supports single-host environments and does not yet support multi-host training.

## Array_record write & read
*A quick start guide for those who are not yet familiar with ArrayRecord.*

```
import numpy as np
from array_record.python.array_record_module import ArrayRecordWriter
from array_record.python.array_record_data_source import ArrayRecordDataSource

train_data = np.load('train_data.npy',mmap_mode='r')
dtype = train_data.dtype
shape =  train_data[0].shape

writer = ArrayRecordWriter("train_data.ar", options="group_size:1,zstd")

for i in range(train_data.shape[0]):
    writer.write(train_data[i].tobytes())

ds = ArrayRecordDataSource("train_data.ar")

np.frombuffer(ds[0], dtype=dtype).reshape(shape)
```

# Quick Start
```
import numpy as np
from loaderx import NPDataset, ARDataset, DataLoader

dataset = ARDataset('xsub/train_data.ar', dtype=np.float32, shape=(3, 300, 25, 2))
labelset = NPDataset('xsub/train_label.npy')

loader = DataLoader(dataset, labelset)

for i, batch in enumerate(loader):
    if i >= 256:
        break
```

## Integrating with Flax

For practical integration examples, please refer to the **Data2Latent** repository:
**[https://github.com/eoeair/Data2Latent](https://github.com/eoeair/Data2Latent)**