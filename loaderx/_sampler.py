import os
import time
import ctypes
import numpy as np
from typing import Union

from lib import libsampler

class Sampler:
    class Mode:
        SEQUENTIAL = 0
        IID = 1

    def __init__(self, length: int, batch_size: int, mode: int, seed: int = 42):
        # sampler
        self.sampler = libsampler.Sampler.init(length, batch_size, mode, seed)
        # indices
        self.indices = np.zeros(batch_size, dtype=np.uint64)

    # step
    def next(self):
        self.sampler.next(self.indices)

    # iterator
    def __iter__(self):
        return self
    def __next__(self):
        self.next()
        return self.indices

def run():
    from itertools import islice
    length = 10
    batch_size = 4
    n_steps = 5

    print("=== Sampler SEQUENTIAL ===")
    sampler = Sampler(length, batch_size, Sampler.Mode.SEQUENTIAL)
    for indices in islice(sampler, n_steps):
        print(indices)

    print("=== Sampler IID ===")
    sampler = Sampler(length, batch_size, Sampler.Mode.IID)
    for indices in islice(sampler, n_steps):
        print(indices)

# Benchmark, zig-sampler speeder 2.2x
def bench():
    length = 1_000_000
    batch_size = 8192
    n_steps = 10_000

    print("=== NumPy IID ===")
    t0 = time.time()
    batch = np.zeros(batch_size, dtype=np.uint64)
    for _ in range(n_steps):
        batch[:] = np.random.randint(0, length, size=batch_size, dtype=np.uint64)
    print(f"{(time.time() - t0)*1000:.2f} ms")

    print("=== Sampler IID ===")
    t0 = time.time()
    sampler = Sampler(length, batch_size, Sampler.Mode.IID)
    for _ in range(n_steps):
        sampler.next()
    print(f"{(time.time() - t0)*1000:.2f} ms")

if __name__ == "__main__":
    run()
    bench()