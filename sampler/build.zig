const std = @import("std");

pub fn build(b: *std.Build) void {
    b.install_prefix = "dist";
    const target = b.standardTargetOptions(.{});
    const optimize = std.builtin.OptimizeMode.ReleaseFast;

    const libsampler = b.addLibrary(.{
        .name = "sampler",
        .linkage = .dynamic,
        .root_module = b.createModule(.{
            .root_source_file = b.path("root.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    b.installArtifact(libsampler);

    // 此处开始构建单元测试
    const test_step = b.step("test", "Run unit tests");

    // 构建一个单元测试的 Compile
    const unit_tests = b.addTest(.{
        .root_module = b.addModule("unit_tests", .{
            .root_source_file = b.path("root.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    const run_unit_tests = b.addRunArtifact(unit_tests);
    test_step.dependOn(&run_unit_tests.step);
}
