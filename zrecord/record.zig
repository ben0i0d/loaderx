const std = @import("std");
const fs = std.fs;
const Allocator = std.mem.Allocator;

pub fn OverwriteDir(
    allocator: Allocator,
    relative_path: []const u8,
) !void {
    const cwd = fs.cwd();
    const dir_path = try fs.path.resolve(allocator, &[_][]const u8{relative_path});
    defer allocator.free(dir_path);

    cwd.deleteTree(dir_path) catch {};
    try cwd.makeDir(dir_path);
}
