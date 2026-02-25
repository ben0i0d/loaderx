const std = @import("std");

pub const Zrecord = struct {
    const Meta = struct { length: u24, chunk_num: u12 };
    const Offset = struct { chunk_id: u12, offset: u32, length: u20 };

    allocator: std.mem.Allocator,
    data_dir: []const u8,

    meta: Meta,
    offset: std.ArrayList(Offset),

    pub fn Init(allocator: std.mem.Allocator, data_dir: []const u8) !Zrecord {
        // Dir prepare
        var buffer: [128]u8 = undefined;
        const cwd = std.fs.cwd();
        try cwd.makeDir(data_dir);

        // File prepare
        const meta = try std.fmt.bufPrint(&buffer, "{s}/meta.json", .{data_dir});
        const file = try cwd.createFile(meta, .{});
        defer file.close();

        // create meta
        return Zrecord{
            .data_dir = data_dir,
            .meta = .{
                .length = 0,
                .chunk_num = 0,
            },
            .offset = std.ArrayList(Offset).init(allocator),
        };
    }

    pub fn AddChunk(self: *Zrecord, chunkid: u12) !void {
        var buffer: [128]u8 = undefined;
        const cwd = std.fs.cwd();

        const chunk = try std.fmt.bufPrint(&buffer, "{s}/{d}.zr", .{ self.data_dir, chunkid });
        const file = try cwd.createFile(chunk, .{});
        defer file.close();

        self.meta.chunk_num += 1;
    }
};

pub fn main() !void {
    try InitDataset("test");
    try AddChunk("test", 0);
}
