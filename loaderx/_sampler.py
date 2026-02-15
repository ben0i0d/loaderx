import os
import time
import ctypes
import numpy as np
from typing import Union

class Sampler:
    
    class Mode:
        SEQUENTIAL = 0
        IID = 1
    
    # lazy import
    _lib = None
    @classmethod
    def _load_lib(cls):
        if cls._lib is None:
            # linux/windows/macos
            names = ['lib/libsampler.so', 'lib/sampler.dll', 'lib/libsampler.dylib']
            lib_paths = [os.path.join(os.path.dirname(__file__), name) for name in names]

            for path in lib_paths:
                if os.path.exists(path):
                        cls._lib = ctypes.CDLL(path)
                        cls._setup_function_signatures()
        return cls._lib
    
    @classmethod
    def _setup_function_signatures(cls):
        lib = cls._lib
        
        # init
        lib.init.argtypes = [
            ctypes.c_void_p,  # sampler
            ctypes.c_uint64,  # length
            ctypes.c_uint64,  # batch_size
            ctypes.c_uint8,   # mode
            ctypes.c_uint64   # seed
        ]
        lib.init.restype = None
        
        # size
        lib.size.restype = ctypes.c_size_t

        # next
        lib.next.argtypes = [
            ctypes.c_void_p,     # sampler
            ctypes.c_void_p      # batch_indices
        ]
        lib.next.restype = None

    def __init__(self, length: int, batch_size: int, mode: int, seed: int = 42):
        # import lib
        self.lib = self._load_lib()

        # sampler
        self.sampler = ctypes.create_string_buffer(self.lib.size())
        self.sampler_ptr = ctypes.cast(self.sampler, ctypes.c_void_p)
        self.lib.init(self.sampler_ptr, length, batch_size, mode, seed)
        
        # batch_indices
        self.indices = np.zeros(batch_size, dtype=np.uint64)
        self.indices_ptr = self.indices.ctypes.data

    # step
    def next(self):
        self.lib.next(self.sampler_ptr, self.indices_ptr)

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