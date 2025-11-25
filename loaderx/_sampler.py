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
            ctypes.c_uint64,  # length
            ctypes.c_uint32,  # batch_size
            ctypes.c_uint8,   # mode
            ctypes.c_uint64   # seed
        ]
        lib.init.restype = ctypes.c_void_p
        
        # deinit
        lib.deinit.argtypes = [ctypes.c_void_p] # sampler
        lib.deinit.restype = None
        
        # next
        lib.next.argtypes = [
            ctypes.c_void_p,                     # sampler
            ctypes.POINTER(ctypes.c_uint64)      # batch_indices
        ]
        lib.next.restype = None

    def __init__(self, length: int, batch_size: int, mode: int, seed: int = 42):
        # import lib
        self.lib = self._load_lib()

        # init sampler
        self.ptr = self.lib.init(length, batch_size, mode, seed)
        if not self.ptr:
            raise RuntimeError(f"Failed to create sampler with params: length={length}, batch_size={batch_size}, mode={mode}, seed={seed}")
        
        # batch_indices
        self.batch_indices = np.zeros(batch_size, dtype=np.uint64)

    # step
    def next(self):
        self.lib.next(self.ptr, self.batch_indices.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)))

    # iterator
    def __iter__(self):
        return self
    def __next__(self):
        self.next()
        return self.batch_indices

    # close
    def deinit(self):
        self.lib.deinit(self.ptr)
    def __del__(self):
        if hasattr(self, 'ptr') and self.ptr:
            self.deinit()

# Benchmark, zig-sampler is better
if __name__ == "__main__":
    length = 1_000_000
    batch_size = 8192
    n_steps = 10_000

    print("=== Python NumPy IID ===")
    t0 = time.time()
    batch = np.zeros(batch_size, dtype=np.uint64)
    for _ in range(n_steps):
        batch[:] = np.random.randint(0, length, size=batch_size, dtype=np.uint64)
    print(f"{(time.time() - t0)*1000:.2f} ms")

    print("=== Sampler IID ===")
    t0 = time.time()
    s = Sampler(length, batch_size, Sampler.Mode.IID)
    for _ in range(n_steps):
        s.next()
    print(f"{(time.time() - t0)*1000:.2f} ms")
    s.deinit()