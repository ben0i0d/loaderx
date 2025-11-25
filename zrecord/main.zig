const std = @import("std");
const zrecord = @import("zrecord.zig");

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    // 允许覆盖
    try zrecord.OverwriteDir(allocator, "data");
}
