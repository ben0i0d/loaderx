const std = @import("std");
const pyoz = @import("PyOZ");

const Sampler = struct {
    length: u64,
    batch_size: u64,
    mode: enum(u8) {
        sequential = 0, // sliding window
        iid = 1, // with replacement
    },

    cursor: u64 = 0,
    rng: std.Random.Sfc64,

    pub fn init(length: u64, batch_size: u64, mode: u8, seed: u64) Sampler {
        return .{
            .length = length,
            .batch_size = batch_size,
            .mode = @enumFromInt(mode),
            .rng = std.Random.Sfc64.init(seed),
        };
    }

    pub fn next(self: *Sampler, batch_indices: pyoz.BufferViewMut(u64)) void {
        switch (self.mode) {
            .sequential => nextSequential(self, batch_indices.data),
            .iid => nextIID(self, batch_indices.data),
        }
    }

    fn nextSequential(self: *Sampler, indices: []u64) void {
        for (0..self.batch_size) |i| {
            indices[i] = (self.cursor + i) % self.length;
        }
        self.cursor = (self.cursor + self.batch_size) % self.length;
    }

    fn nextIID(self: *Sampler, indices: []u64) void {
        const rng = self.rng.random();

        for (0..self.batch_size) |i| {
            indices[i] = rng.int(u64) % self.length;
        }
    }
};

// ============================================================================
// Module definition
// ============================================================================
pub const Module = pyoz.module(.{
    .name = "Sampler",
    .doc = "Sampler with Zig",
    .funcs = &.{},
    .classes = &.{
        pyoz.class("Sampler", Sampler),
    },
});

pub export fn PyInit_libsampler() ?*pyoz.PyObject {
    return Module.init();
}
