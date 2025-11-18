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
3. A NumPy-based implementation for excellent compatibility with JAX.
4. An **immortal (endless) step-based data loader**, rather than the traditional epoch-based design—better aligned with modern ML training practices.

## Current Limitations

Currently, loaderx only supports single-host environments and does not yet support multi-host training.

## Integrating with Flax

For practical integration examples, please refer to the **Data2Latent** repository:
**[https://github.com/eoeair/Data2Latent](https://github.com/eoeair/Data2Latent)**