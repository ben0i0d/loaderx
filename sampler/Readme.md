# 构建

zig build-lib sampler.zig -dynamic

# 索引生成器

为zrecord生成indices,替代python实现以提高性能

需要注意的是，loaderx设计为step-based、永久生命的数据加载器，因此我们不考虑epoch等概念

## 顺序生成

indices在索引空间中遍历得到

1. 滑动遍历：indices由一个定长滑动窗口得到，但是注意，此时索引空间变为环形队列来避免尾截断

## 随机生成

结合工业实践（参考Torch DistributedSampler + BatchSampler），近似全局随机是默认推荐策略，SGD不会受到影响

1. 全局随机：全局随机得到一组样本
2. 近似全局随机：由于block是对全局空间的顺序子集，因此全局随机可以在每个block内随机产生，这同时可以避免grouped负担