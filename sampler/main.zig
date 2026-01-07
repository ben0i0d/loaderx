const std = @import("std");
const sampler = @import("sampler.zig");

pub fn main() !void {
    const num_samples = 10;
    const batch_size = 4;

    var buffer: [batch_size]usize = undefined;

    // ===== 顺序滑动（环形）=====
    std.debug.print("Sequential (circular):\n", .{});
    var seq = sampler.Sampler.init(
        num_samples,
        batch_size,
        .sequential,
        0,
    );

    var step: usize = 0;
    while (step < 5) : (step += 1) {
        seq.next(&buffer);
        std.debug.print("step {d}: {any}\n", .{ step, buffer });
    }

    // ===== 全局随机 =====
    std.debug.print("\nRandom (global):\n", .{});
    var rnd = sampler.Sampler.init(
        num_samples,
        batch_size,
        .random,
        12345,
    );

    step = 0;
    while (step < 5) : (step += 1) {
        rnd.next(&buffer);
        std.debug.print("step {d}: {any}\n", .{ step, buffer });
    }
}
