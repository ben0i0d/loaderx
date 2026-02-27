const std = @import("std");
const pyoz = @import("PyOZ");

const Header = struct {
    length: u24,
    chunk_num: u12,
    compress: enum(u8) {
        raw = 0,
        flate = 1,
    },
    pad: u20,
};

const Offset = struct {
    chunk_id: u12,
    offset: u32,
    physical_length: u20,
};

const WriteTask = union(enum) {
    append: pyoz.ByteArray,
    modify: struct { index: u32, record: pyoz.ByteArray },
    delete: u32,
};

const ReadTask = struct {
    batch: []pyoz.ByteArray,
    pos: u32,
    offset: Offset,
};

pub const Zrecord = struct {
    allocator: std.mem.Allocator,
    data_dir: []const u8,

    header: Header,
    offset: std.ArrayList(Offset),
    chunk: std.ArrayList([]u8),
    batch: std.ArrayList([]pyoz.ByteArray),

    write_queue: std.Io.Queue(WriteTask),
    read_queue: std.Io.Queue(ReadTask),
    gc_queue: std.Io.Queue([]pyoz.ByteArray),

    pub fn Init(allocator: std.mem.Allocator, data_dir: []const u8, compress: u8, batch_size: u32) !Zrecord {
        // Dir prepare
        const cwd = std.fs.cwd();
        try cwd.makeDir(data_dir);

        // create meta
        return Zrecord{
            .allocator = allocator,
            .data_dir = data_dir,

            .header = .{
                .length = 0,
                .chunk_num = 0,
                .compress = @enumFromInt(compress),
                .pad = 0,
            },
            .offset = std.ArrayList(Offset).init(allocator),
            .chunk = std.ArrayList([]u8).init(allocator),
            .batch = std.ArrayList([batch_size]pyoz.ByteArray).init(allocator),

            .batch_size = 0,
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
