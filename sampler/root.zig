const std = @import("std");

pub const Sampler = struct {
    length: u64,
    batch_size: u64,
    mode: enum(u8) {
        sequential = 0, // sliding window
        iid = 1, // with replacement
    },

    cursor: u64 = 0,
    rng: std.Random.Sfc64,
};

pub export fn init(
    self: *Sampler,
    length: u64,
    batch_size: u64,
    mode: u8,
    seed: u64,
) void {
    self.* = Sampler{
        .length = length,
        .batch_size = batch_size,
        .mode = @enumFromInt(mode),
        .rng = std.Random.Sfc64.init(seed),
    };
}

pub export fn size() usize {
    return @sizeOf(Sampler);
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

// unit tests
fn run(mode: u8) void {
    const length = 10;
    const batch_size = 4;

    var buffer: [batch_size]u64 = undefined;

    var sampler: Sampler = undefined;
    init(&sampler, length, batch_size, mode, 0);

    std.debug.print("Mode: {any}\n", .{mode});
    var step: usize = 0;
    while (step < 5) : (step += 1) {
        next(&sampler, &buffer);
        std.debug.print("step {d}: {any}\n", .{ step, buffer });
    }
}

test "runSampler" {
    std.debug.print("Size: {d}\n", .{size()});
    run(0);
    run(1);
}
