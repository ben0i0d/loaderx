# 测试运行

zig run main.zig

# 构建

zig build-lib sampler.zig -dynamic

# 索引生成器

为loaderx生成indices,替代python实现以提高性能

需要注意的是，loaderx设计为step-based、永久生命的数据加载器，因此每调用一次只需要返回一个batch_size的索引序列

## 顺序生成

indices在索引空间中遍历得到

1. 滑动遍历：indices由一个定长滑动窗口得到，但是注意，此时索引空间变为环形队列来避免尾截断

## 随机生成

1. 全局随机：全局随机得到一组样本