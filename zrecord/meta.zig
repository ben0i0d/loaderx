const std = @import("std");

pub const Offset = []struct { chunk_id: u32, offset: u64, length: u32 };

pub const Meta = struct {
    length: u64,
    chunks: []struct {
        num: u32,
        size: u32,
        unfull: []struct { chunkid: u32, write_pos: u64, record_count: u32 },
    },
    fields: []struct {
        name: []const u8,
        dtype: enum(u8) { i32 = 0, i64 = 1, f16 = 2, f32 = 3, f64 = 4 },
        compress: enum(u8) { raw = 0, flate = 1 },
    },
};

pub fn InitDataset(root_path: []const u8) !Meta {
    // create meta
    const meta = Meta{
        .length = 0,
        .chunks = &.{},
        .fields = &.{},
    };
    // File prepare
    var buffer: [2][128]u8 = undefined;
    const cwd = std.fs.cwd();

    const meta_path = try std.fmt.bufPrint(&buffer[0], "{s}/meta.json", .{root_path});
    const chunk_path = try std.fmt.bufPrint(&buffer[1], "{s}/chunk", .{root_path});

    try cwd.makeDir(root_path);
    try cwd.makeDir(chunk_path);
    const file = try cwd.createFile(meta_path, .{});
    defer file.close();

    return meta;
}

pub fn AddChunk(root_path: []const u8, chunkid: u32) !void {
    var buffer: [128]u8 = undefined;
    const cwd = std.fs.cwd();
    const chunk = try std.fmt.bufPrint(&buffer, "{s}/chunk/{d}.zr", .{ root_path, chunkid });

    const file = try cwd.createFile(chunk, .{});
    defer file.close();
}

pub fn AddOffset(root_path: []const u8, field: []const u8) !void {
    var buffer: [128]u8 = undefined;
    const cwd = std.fs.cwd();
    const offset = try std.fmt.bufPrint(&buffer, "{s}/{s}.offset", .{ root_path, field });

    const file = try cwd.createFile(offset, .{});
    defer file.close();
}

pub fn main() !void {
    try InitDataset("test");
    try AddChunk("test", 0);
    try AddOffset("test", "data");
}
