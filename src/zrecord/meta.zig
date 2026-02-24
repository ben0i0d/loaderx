const std = @import("std");

pub const Offset = []struct { chunk_id: u12, offset: u32, length: u20 };

pub const Meta = struct { length: u24, chunk_num: u12 };

pub fn InitDataset(root_path: []const u8) !Meta {
    // Dir prepare
    var buffer: [3][128]u8 = undefined;
    const cwd = std.fs.cwd();
    try cwd.makeDir(root_path);

    // File prepare
    const meta_path = try std.fmt.bufPrint(&buffer[0], "{s}/meta.json", .{root_path});
    const meta = try cwd.createFile(meta_path, .{});
    defer meta.close();

    // create meta
    return Meta{
        .length = 0,
        .chunk_num = 0,
    };
}

pub fn AddChunk(root_path: []const u8, chunkid: u32) !void {
    var buffer: [128]u8 = undefined;
    const cwd = std.fs.cwd();
    const chunk = try std.fmt.bufPrint(&buffer, "{s}/{d}.zr", .{ root_path, chunkid });

    const file = try cwd.createFile(chunk, .{});
    defer file.close();
}

pub fn main() !void {
    try InitDataset("test");
    try AddChunk("test", 0);
}
