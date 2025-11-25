const std = @import("std");
const Sampler = @import("root.zig");

fn runSampler(mode: u8) !void {
    const length = 10;
    const batch_size = 4;

    const buffer = try std.heap.page_allocator.alloc(u64, batch_size);
    defer std.heap.page_allocator.free(buffer);

    const s_opt = Sampler.init(length, batch_size, mode, 0);
    if (s_opt == null) return error.OutOfMemory;
    const s = s_opt.?; // unwrap
    defer Sampler.deinit(s);

    std.debug.print("Mode: {any}\n", .{mode});
    var step: usize = 0;
    while (step < 5) : (step += 1) {
        Sampler.next(s, buffer.ptr);
        std.debug.print("step {d}: {any}\n", .{ step, buffer });
    }
}

fn benchSampler(mode: u8) !void {
    const length = 1_000_000;
    const batch_size = 8192;

    const buffer = try std.heap.page_allocator.alloc(u64, batch_size);
    defer std.heap.page_allocator.free(buffer);

    const s_opt = Sampler.init(length, batch_size, mode, 0);
    if (s_opt == null) return error.OutOfMemory;
    const s = s_opt.?;
    defer Sampler.deinit(s);

    var timer = try std.time.Timer.start();
    // bench 1e4
    for (0..10_000) |_| _ = Sampler.next(s, buffer.ptr);
    const ms = @as(f64, @floatFromInt(timer.read())) / 1_000_000;
    std.debug.print("{any}: {d} ms\n", .{ mode, ms });
}

pub fn main() !void {
    try runSampler(1);
    try benchSampler(1);
}
