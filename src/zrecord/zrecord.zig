const std = @import("std");

pub const Zrecord = struct {
    const Header = struct { length: u24, chunk_num: u12, compress: enum(u8) { raw = 0, flate = 1 }, _pad: u20 };
    const Offset = struct { chunk_id: u12, offset: u32, length: u20 };

    allocator: std.mem.Allocator,
    data_dir: []const u8,

    header: Header,
    offset: std.ArrayList(Offset),

    pub fn Init(allocator: std.mem.Allocator, data_dir: []const u8, compress: u8) !Zrecord {
        // Dir prepare
        const cwd = std.fs.cwd();
        try cwd.makeDir(data_dir);

        // create meta
        return Zrecord{
            .data_dir = data_dir,
            .header = .{
                .length = 0,
                .chunk_num = 0,
                .compress = @enumFromInt(compress),
                .pad = 0,
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

        self.header.chunk_num += 1;
    }
};

pub fn main() !void {
    try Zrecord.Init("test");
    try Zrecord.AddChunk("test", 0);
}
