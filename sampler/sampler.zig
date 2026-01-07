const std = @import("std");

pub const Mode = enum {
    sequential,
    random,
};

pub const Sampler = struct {
    num_samples: usize,
    batch_size: usize,
    mode: Mode,

    // sequential
    cursor: usize = 0,

    // random
    prng: std.rand.DefaultPrng,

    pub fn init(
        num_samples: usize,
        batch_size: usize,
        mode: Mode,
        seed: u64,
    ) Sampler {
        return Sampler{
            .num_samples = num_samples,
            .batch_size = batch_size,
            .mode = mode,
            .cursor = 0,
            .prng = std.rand.DefaultPrng.init(seed),
        };
    }

    /// 每次调用只生成一个 batch
    /// out.len 必须 == batch_size
    pub fn next(self: *Sampler, out: []usize) void {
        std.debug.assert(out.len == self.batch_size);

        switch (self.mode) {
            .sequential => self.nextSequential(out),
            .random => self.nextRandom(out),
        }
    }

    fn nextSequential(self: *Sampler, out: []usize) void {
        var i: usize = 0;
        while (i < out.len) : (i += 1) {
            out[i] = (self.cursor + i) % self.num_samples;
        }
        self.cursor = (self.cursor + out.len) % self.num_samples;
    }

    fn nextRandom(self: *Sampler, out: []usize) void {
        var rng = self.prng.random();
        var i: usize = 0;
        while (i < out.len) : (i += 1) {
            out[i] = rng.uintLessThan(usize, self.num_samples);
        }
    }
};

/// ===== C ABI（可选，用于 loaderx / Python FFI）=====
export fn sampler_create(
    num_samples: usize,
    batch_size: usize,
    mode: u32, // 0 = sequential, 1 = random
    seed: u64,
) *Sampler {
    const allocator = std.heap.c_allocator;

    var sampler = allocator.create(Sampler) catch return null;
    sampler.* = Sampler.init(
        num_samples,
        batch_size,
        if (mode == 0) .sequential else .random,
        seed,
    );
    return sampler;
}

export fn sampler_next(
    sampler: *Sampler,
    out_ptr: [*]usize,
) void {
    sampler.next(out_ptr[0..sampler.batch_size]);
}

export fn sampler_destroy(sampler: *Sampler) void {
    const allocator = std.heap.c_allocator;
    allocator.destroy(sampler);
}
