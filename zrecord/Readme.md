# 设计思想

在保持 ArrayRecord 使用习惯的前提下，提供一个并发友好、实现更简单、单机性能更优的 record 存储格式，用于替代 ArrayRecord 并解决其并发读取瓶颈

1. ZRecord 面向机器学习场景，原生基于 record 思想设计，我们不假定record间存在顺序关系
2. 每个 record 是相互独立的逻辑记录，但在 Python 侧提供与 NumPy 兼容的 array 接口投影，以便无缝集成现有 ML 生态
3. block 文件是并行与隔离的最小单位

# 存储形式
1. ZRecord 仅包含一个多流数据集，长度为 N（N 个 record）
    * 索引空间为 [0, N)，所有索引与切块语义等价于 gather 操作
    * 多流，类似 `set['A'], set['B']`, 但必须等长
    ```
    Dataset:
    record_id = 0..N-1

    Field A: bytes / tensor / audio / text
    Field B: bytes / label / meta
    ```
2. 为降低存储体积，支持粒度为record级的透明压缩，以下是可选的压缩方法
```
| 方法  | 算法    |
| ----- | ------- |
| raw   | 无压缩  | 
| flate | Deflate | 
```
3. record通常是不定长的，通过indirection支持高级操作（删除/覆盖/插入），offset支持高效随机访问
    * indirection表是一个列表 [idx : u32, ...]，长度为N。将外部索引空间（outside[0, N]）指向一个内部索引空间
        * idx默认类型为u32：idx类型由数据集长度合理得出
        ```
        u8   →   255
        u16  →   65535
        u32  →   4.29e9
        u64  →   1.84e19
        ```
    ```
    outside idx (global)
    ↓
    ↓indirection[idx] = physical_id
    ↓
    block_id = physical_id // block_size
    local_idx = physical_id % block_size
    ↓
    offset[local_idx] → (offset, length)
    ```
    * offset表是一个三元组 [[offset : u64, physical_length : u32, logical_length : u32] ...]，长度<=block_size
        * offset表内元素类型与存储大小有关，offset类型由block文件大小合理得出，length（physical_length/logical_length）由record大小合理得出
        * offset默认类型为u64
        * length（physical_length/logical_length）默认类型为u32
            * physical_length是record写入长度
            * logical_length是record原始长度（无压缩情况下，physical_length==logical_length）
        ```
        u8   →   255 B
        u16  →   64 KB
        u32  →   4 GB
        u64  →   16 EB
        ```
4. 为规避文件系统 IO 锁与并发瓶颈，ZRecord的存储是元数据+分块的格式
    1. 元数据
        * meta.json：描述全局元数据，包括全局参数（版本、数据集长度、分块大小、间接索引表类型）与Field参数
        ```
        {
        "version": 1,
        "length": 65536,
        "block_size": 8192,
        "indirection_dtype": "u32",
        "fields": {
            "A": {"dtype": "f32", "compressed": "zstd", "offset_dtype": "u64", "length_dtype": "u32"}
            "B": {"dtype": "i32", "compressed": "raw", "offset_dtype": "u32", "length_dtype": "u8"}
        }
        }
        ```
        * indirection.zr：间接索引表
        * offset/Field_x.zr: 每个block的offset表
        ```
        0 255
        256 511
        ...
        ```
    2. 分块数据
        * block/Field_x.zr: 包含最多 block_size 个 record

存储格式如下
```
dataset
  ├── meta.json
  ├── indirection.zr
  ├── offset
  │    ├── A_0.zr
  │    └── B_1.zr
  ├── block
  │    ├── A_0.zr
  └──└── B_1.zr
```

# 调度器

负责同步执行写任务并维护RAL队列

1. RAL(Read Access Log)队列：每个block持有独立block_id_RAL无竞态队列，支持异步
2. 任务（Task）：
    * 写任务调用对应线程同步执行，确保不引入不确定性
    * 读任务压入block_id_RAL, [idx, ...] --> block_id - [[local_idx, ...]]
3. 调度规则（block 级并行，share-nothing）
    * 每个 block 在任一时刻只由一个工作线程处理, block 数 = 线程数  → 一 block 一线程
    * 工作线程异步从block_id_RAL队列中提取任务

# 任务

## 写任务

写入只允许append-only,所有高级操作基于对indirection的重定向，同时注意所有写入都必须同时提供所有field参数

1. 追加：追加一个数据，record追加到最后一个block末尾，offset表追加条目，如果超过block_size,则新建block
    * 调用block_id_Thread append方法, 检验是否需要新建block, 增加末尾record, 追加offset条目，新的offset是前一条offset+length/0,length是压缩后bytes长度，全局长度增加

2. 修改：追加一个record，并修改indirection项

3. 删除：删除indirection项

4. 插入：追加一个record，并插入indirection项

## 读任务

用一个indices（索引数组），从原数组里访问指定位置的元素

1. IO 与解压阶段分离，避免在同一执行路径中混合 IO 密集型与 CPU 密集型任务
2. 数据类型支持
    * 整数：  i32
    * 单精度：f32
    * 半精度：f16 
3. 对于无压缩的数据，将直接返回文件内地址实现zero-copy

读取流程
```
[idx0, idx1, ...]
↓
[(0, idx0), (1, idx1), ...]
↓
[(0, physical_idx0), (1, physical_idx1), ...]
↓
[(0, block_id0, local_idx0), (1, block_id1, local_idx1), ...]
↓
block 0 → [(0, local_idx0), (1, local_idx1), ...]
block 1 → [(2, local_idx0), (3, local_idx1), ...]
↓
[(ptr0, length0), (ptr1, length1), ...]
```

## 维护任务

1. 垃圾回收（GC）：indirection经过大量操作后，会出现空洞,通过垃圾回收来回收资源
    * 实现：根据indirection进行重写入，并在完成后替换
    * GC只允许手动运行，确保用户知情，这被设计为一个离线操作，但提供一个计算垃圾占比（无效bytes/总bytes）的函数