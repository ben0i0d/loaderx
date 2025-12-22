const std = @import("std");

pub const Mode = enum {
    Sequential,
    RandomApprox,
};

pub const Sampler = struct {
    n: usize,
    batch_size: usize,
    step: u64,
    mode: Mode,

    rng: std.Random.DefaultPrng,

    block: []usize,
    block_size: usize,
    usable_block: usize,
    block_id: usize,

    allocator: std.mem.Allocator,

    pub fn init(
        allocator: std.mem.Allocator,
        n: usize,
        batch_size: usize,
        mode: Mode,
        seed: u64,
    ) !Sampler {
        const rng = std.Random.DefaultPrng.init(seed);

        var block_size = batch_size * 8;
        if (block_size > n) block_size = n;

        const usable_block = (block_size / batch_size) * batch_size;
        std.debug.assert(usable_block >= batch_size);

        const block = try allocator.alloc(usize, block_size);

        return Sampler{
            .n = n,
            .batch_size = batch_size,
            .step = 0,
            .mode = mode,
            .rng = rng,
            .block = block,
            .block_size = block_size,
            .usable_block = usable_block,
            .block_id = 0,
            .allocator = allocator,
        };
    }

    pub fn deinit(self: *Sampler) void {
        self.allocator.free(self.block);
    }

    pub fn next(self: *Sampler, out: []usize) void {
        switch (self.mode) {
            .Sequential => self.nextSequential(out),
            .RandomApprox => self.nextRandomApprox(out),
        }
        self.step += 1;
    }

    // ======================
    // 顺序 + 环形滑动窗口
    // ======================
    fn nextSequential(self: *Sampler, out: []usize) void {
        const start = self.step * self.batch_size;

        var i: usize = 0;
        while (i < self.batch_size) : (i += 1) {
            out[i] = (start + i) % self.n;
        }
    }

    // ======================
    // 近似全局随机
    // ======================
    fn refillBlock(self: *Sampler) void {
        const start = (self.block_id * self.block_size) % self.n;

        var i: usize = 0;
        while (i < self.block_size) : (i += 1) {
            self.block[i] = (start + i) % self.n;
        }

        // Fisher–Yates shuffle
        var rnd = self.rng.random();
        i = self.block_size;
        while (i > 1) {
            i -= 1;
            const j = rnd.uintLessThan(usize, i + 1);
            std.mem.swap(usize, &self.block[i], &self.block[j]);
        }

        self.block_id += 1;
    }

    fn nextRandomApprox(self: *Sampler, out: []usize) void {
        const offset = (self.step * self.batch_size) % self.usable_block;

        if (offset == 0) {
            self.refillBlock();
        }

        var i: usize = 0;
        while (i < self.batch_size) : (i += 1) {
            out[i] = self.block[offset + i];
        }
    }
};
