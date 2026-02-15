# loaderx
A record-based data runtime, focused on delivering extreme throughput and low latency

**Only Python3.13_Linux_amd64**

## Sampler
a high-performance sampler implemented in Zig
### Index Generator
1. Sequential generation: indices are produced by traversing the index space in order.
    * Sliding traversal: indices are obtained using a fixed-size sliding window. Note that in this case, the index space is treated as a circular queue to avoid truncation at the tail.
2. Random generation: indices are sampled randomly from the index space.
    * Global random: a set of samples is drawn randomly from the entire index space.

## zrecord
基于Zig实现一个并发友好、实现更简单、单机性能更优的 record 存储系统

1. ZRecord基于 record 思想设计，我们不假定record间存在顺序关系，对于顺序语义应在record内部表达或建立timestamp
2. record是相互独立的逻辑记录，仅在 Python 侧提供与 NumPy 兼容的 array 接口投影
3. zrecord是无类型的，数据只是Bytes，类型解析由上层完成
4. chunk只是存储管理单元，提高并发性能，不具备语义

### 存储形式
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
3. 通过offset支持高效随机访问
    * offset表项是一个三元组 [[chunk_id : u32, offset : u64, physical_length : u32], ...]，长度为N。将外部索引空间（outside[0, N]）指向一个实际存储地址
        * chunk_id为u32，表示具体chunk
        * offset为u64, 表示具体chunk内的偏移
        * physical_length为u32，表示record数据大小
        * offset表每项的字节大小最好为 8 的整数倍，提升对齐和缓存效率
        * offset表是mmap访问模式，由于等长，直接将 idx 转换为 ptr + 16*idx
        * 不同位宽表示的数值范围
        ```
        u16 → 2^16 - 1 （65535）
        u32 → 2^32 - 1 （4.29e9）
        u64 → 2^64 - 1 （1.84e19）
        ```
        * 不同位宽表示的数据大小
        ```
        u16 → 64 KiB
        u32 → 4 GiB
        u64 → 16 EiB
        ```
    ```
    outside idx (global)
    ↓
    ↓offset[idx]
    ↓
    chunk_id, offset, physical_length
    ```
4. ZRecord的存储是元数据+分块的格式
    1. 元数据
        * meta.json：描述全局元数据，包括全局参数与Field参数
        ```
        {
        "length": 65536,
        "chunks": { "num": 12, "size": 8192, "unfull": {[8, write_pos, record_count], ... } },
        "fields": [ {"name": "A", "dtype": "f32", "compress": "flate"}, {"name": "B", "dtype": "i32", "compress": "raw"} ]
        }
        ```
        * Field_offset.zr：索引表
        ```
        0 0 255
        0 256 511
        ...
        ```
    2. 分块数据
        * chunk/x.zr: 分块的chunk数据,chunk不区分数据所属

存储格式如下
```
dataset
  ├── meta.json
  ├── A.offset
  ├── B.offset
  ├── chunk
  │    ├── 0.zr
  └──└── 1.zr
```

### 执行器

负责维护任务队列，工作线程，handle

1. 任务队列：
    * write_task：写任务队列，压入[ops, record]，等待writer弹出
    * read_task：读任务队列，预分配batch并压入[batch, pos, chunk_id, offset, physical_length]，等待reader弹出
        * batch: 具体读取请求下创建的与indices等长的二元组
        * pos：在batch中的位置，保证等序返回
    * gc_task：垃圾回收任务队列，压入batch，等待cleaner弹出

2. 工作线程：执行具体任务的工作线程
    * writer：线程池执行写任务，但每个线程固定对应一个chunk
        * writer只会向自己的chunk写入（写满时新建chunk提交给执行器完成）
        * num_writer推荐：1-4
    * reader：线程池执行读任务
        * num_reader推荐：8-32
    * cleaner：线程池执行垃圾回收任务
        * num_cleaner推荐：2-4

3. handle：
    1. mmap：维护全局offset、chunk文件的handle
        * 初始化阶段注册,关闭前释放
        * 对于full的chunk,使用mmap+close（只读），对于unfull的chunk使用mmap（读写）。一旦写满（writer提交），新建chunk并返回给writer,原mmap close。（避免过多占用fd）
        * 对于chunk/offset文件，动态完成分块增长，基于ftruncate+mremap实现
            * 扩容offset表，一次增长 1M项（16MiB）
            * 扩容chunk文件，一次增长 1GiB
    2. batch：维护每次返回batch的handle,也就是[ptr, logical_length]中ptr的合规性
        * 工作线程完成后注册
        * 必须调用函数来手动释放，释放时batch压入GC队列

#### 在线任务

1. 写任务：写入只允许chunk-level append-only,其余操作基于offset重定向，缺失的field构造为全为0的项（physical_length为0代表无）
    1. 追加：在chunk当前写入位置追加一个record，offset表更新length+1条目，全局长度增加
        * 写满：写入完成时检查，如果record_count达到chunk_size, 新建chunk
        * 写入越界：捕捉错误，并对chunk扩容
        * offset[ length+1 ]不存在：捕捉错误，并对offset扩容
    2. 修改：追加一个record，并修改offset项
    3. 删除：删除offset项(将目标项替换为最后一项)，length减一（越界访问属于UB行为）

2. 读任务：用一个indices（索引数组），从原数组里访问指定位置的元素(gather)
    1. 对于无压缩的数据，将直接返回文件内地址实现zero-copy

    读取流程
    ```
    [idx]
    ↓
    [batch, pos, idx]
    ↓field_offset
    [batch, pos, chunk_id, offset, physical_length]
    ↓
    [ptr, logical_length]
    ```

3. 垃圾回收任务：cleaner从GC队列中释放对应batch
    1. 对于无压缩的数据，不释放内存，只释放 batch 本身
    2. 对于有压缩的数据，释放内存
    3. GC后访问ptr属于UB行为

#### 离线任务

1. 重平衡（Rebalance）：zrecord经过大量写操作后，会出现chunk访问不平衡,通过重平衡来恢复chunk的可访问性
    * 实现：根据offset进行重写入，并在完成后替换
    * Rebalance只允许手动运行，确保用户知情，提供一个利用率（sum(length)/sum(chunk_size*num_chunks)）

### 分布式扩展

**该部分暂时不会实现，只是提前架构**

1. 分布式下，我们会得到一个更高的层次-cluster,单机将变为cluster内的node
2. node持有一个shard,包含若干个chunk
3. 添加一个indirection表，将全局路径映射到具体node的表，indirection也可以使用hash实现，从而无锁，索引路径变为
```
outside idx (global)
↓
↓indirection[idx]
↓
node, idx
↓
↓offset[idx]
↓
chunk_id, offset, physical_length
```

## Convert a NumPy tensor to Array_record

*This will create a directory containing file shards, which helps improve I/O performance.*

```
import numpy as np
from loaderx import converter

train_data = np.load('train_data.npy',mmap_mode='r')
converter(train_data, 'train_data')
```

## Current Limitations
Currently, loaderx only supports single-host environments and does not yet support multi-host training.

## Quick Start
```
import numpy as np
from loaderx import NPDataset, ARDataset, DataLoader

dataset = ARDataset('train_data')
labelset = NPDataset('xsub/train_label.npy')

loader = DataLoader(dataset, labelset)

for i, batch in enumerate(loader):
    if i >= 256:
        break

print(batch['data'].shape)
print(batch['label'].shape)
```

### Integrating with JAX/Flax

For practical integration examples, please refer to the **[Data2Latent](https://codeberg.org/eoelab/Data2Latent)** repository