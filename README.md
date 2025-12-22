# loaderx
A compact and high-performance single-machine data loader designed for JAX/Flax.

Currently, **loaderx** is divided into three components:

* **loaderx**: the data loader and the final user-facing interface
* **sampler**: a high-performance sampler implemented in Zig
* **zrecord**: a record storage format that is concurrency-friendly, simpler to implement, and offers better single-machine performance, designed to replace ArrayRecord and address its concurrent read bottleneck

The project is currently undergoing an experimental high-performance refactor. Please use the package published on PyPI as the authoritative source, and do not use the repository directly.
