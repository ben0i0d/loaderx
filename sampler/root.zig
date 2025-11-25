const std = @import("std");

pub const Mode = enum(u8) {
    sequential = 0, // sliding window
    iid = 1, // with replacement
};

pub const Sampler = struct {
    length: u64,
    batch_size: u32,
    mode: Mode,

    cursor: usize = 0,
    rng: std.Random.Sfc64,
};

pub export fn init(
    length: u64,
    batch_size: u32,
    mode: u8,
    seed: u64,
) ?*Sampler {
    const self = std.heap.page_allocator.create(Sampler) catch return null;

    self.* = .{
        .length = length,
        .batch_size = batch_size,
        .mode = @enumFromInt(mode),
        .rng = std.Random.Sfc64.init(seed),
    };

    return self;
}

pub export fn deinit(self: *Sampler) void {
    std.heap.page_allocator.destroy(self);
}

pub export fn next(self: *Sampler, batch_indices: [*]u64) void {
    switch (self.mode) {
        .sequential => nextSequential(self, batch_indices[0..self.batch_size]),
        .iid => nextIID(self, batch_indices[0..self.batch_size]),
    }
}

fn nextSequential(self: *Sampler, batch_indices: []u64) void {
    for (0..self.batch_size) |i| {
        batch_indices[i] = (self.cursor + i) % self.length;
    }
    self.cursor = (self.cursor + self.batch_size) % self.length;
}

fn nextIID(self: *Sampler, batch_indices: []u64) void {
    const rng = self.rng.random();

    for (0..self.batch_size) |i| {
        batch_indices[i] = rng.int(u64) % self.length;
    }
}
