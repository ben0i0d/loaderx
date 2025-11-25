const std = @import("std");

pub fn OverwriteDir(
    allocator: std.mem.Allocator,
    relative_path: []const u8,
) !void {
    const cwd = std.fs.cwd();
    const dir_path = try std.fs.path.resolve(allocator, &[_][]const u8{relative_path});
    defer allocator.free(dir_path);

    cwd.deleteTree(dir_path) catch {};
    try cwd.makeDir(dir_path);
}

pub const Meta = struct {
    version: u8,
    length: u64,
    chunk_size: u32,
    fields: []struct { name: []const u8, dtype: []const u8, compress: []const u8 },
};

pub const Offset = []struct { chunk_id: u16, offset: u40, length: u24 };
