const std = @import("std");
const sampler = @import("sampler.zig");

pub fn main() !void {
    const allocator = std.heap.page_allocator;

    const n = 10;
    const batch_size = 4;
    var buf: [batch_size]usize = undefined;

    // ======================
    // 顺序模式测试
    // ======================
    {
        std.debug.print("=== Sequential (ring) ===\n", .{});
        var s = try sampler.Sampler.init(
            allocator,
            n,
            batch_size,
            .Sequential,
            0,
        );
        defer s.deinit();

        var step: usize = 0;
        while (step < 6) : (step += 1) {
            s.next(buf[0..]);
            std.debug.print("step {d}: {any}\n", .{ step, buf });
        }
    }

    // ======================
    // 近似全局随机测试
    // ======================
    {
        std.debug.print("\n=== Random Approx (block shuffle) ===\n", .{});
        var s = try sampler.Sampler.init(
            allocator,
            n,
            batch_size,
            .RandomApprox,
            1234,
        );
        defer s.deinit();

        var step: usize = 0;
        while (step < 6) : (step += 1) {
            s.next(buf[0..]);
            std.debug.print("step {d}: {any}\n", .{ step, buf });
        }
    }
}
