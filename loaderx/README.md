# loaderx
A compact and high-performance single-machine data loader designed for JAX/Flax.

## Why Create loaderx?

While JAX/Flax supports multiple data-loading backends—including PyTorch, TensorFlow, Grain, and jax_dataloader—each comes with notable drawbacks:

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

## Convert a NumPy tensor to Array_record

*This will create a directory containing file shards, which helps improve I/O performance.*

```
import numpy as np
from loaderx import converter

train_data = np.load('train_data.npy',mmap_mode='r')
converter(train_data, 'train_data')
```

# Quick Start
```
import numpy as np
from loaderx import NPDataset, ARDataset, DataLoader

dataset = ARDataset('train_data')
labelset = NPDataset('xsub/train_label.npy')

print(dataset[0])

loader = DataLoader(dataset, labelset)

for i, batch in enumerate(loader):
    if i >= 256:
        break

print(batch['data'].shape)
print(batch['label'].shape)
```

## Integrating with JAX/Flax

For practical integration examples, please refer to the **[Data2Latent](https://github.com/eoeair/Data2Latent)** repository