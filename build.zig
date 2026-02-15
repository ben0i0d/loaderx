const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = std.builtin.OptimizeMode.ReleaseFast;

    // For `zig build`, pass: -Dpython-version=python3.13
    const pythonversion_opt = b.option([]const u8, "python-version", "Python version");
    const pythonversion = pythonversion_opt orelse "python3.13";

    const pyoz = b.dependency("PyOZ", .{
        .target = target,
        .optimize = optimize,
    });

    const libsampler = b.addLibrary(.{
        .name = "sampler",
        .linkage = .dynamic,
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/sampler/root.zig"),
            .target = target,
            .optimize = optimize,
            .imports = &.{
                .{ .name = "PyOZ", .module = pyoz.module("PyOZ") },
            },
        }),
    });
    // Link Python
    libsampler.linkSystemLibrary(pythonversion);

    b.installArtifact(libsampler);
}
