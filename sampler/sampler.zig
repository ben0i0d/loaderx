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
    prng: std.Random.DefaultPrng,

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
            .prng = std.Random.DefaultPrng.init(seed),
        };
    }

    /// out.len == batch_size
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
