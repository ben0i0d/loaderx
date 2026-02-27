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
基于Zig实现一个并发友好、实现简单、性能更优的 record 存储系统

1. zrecord默认record相互独立，不假定record间存在顺序关系
2. zrecord向Python 侧返回 NumPy Array，但类型解析由Numpy完成
3. zrecord仅包含一个数据集，长度为 N（N 个 record），所有索引与切块语义等价于 gather 操作
4. zrecord是数据运行时，并不是数据存储引擎，因此将以内存数据为主状态，仅定期持久化到文件系统中
5. 为降低存储体积，支持record级透明压缩，以下是可选的压缩方法
```
| 方法  | 算法    |
| ----- | ------- |
| raw   | 无压缩  | 
| flate | Deflate | 
```

### 运行时格式
ZRecord运行时以内存状态为主，定期持久化保存
```
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

pub const Zrecord = struct {
    allocator: std.mem.Allocator,
    data_dir: []const u8,

    header: Header,
    offset: std.ArrayList(Offset),
    chunk: std.ArrayList([]u8),
};
```

### 持久化格式
ZRecord的存储是元数据+分块数据的格式，存储格式如下
```
dataset/
  ├── meta.zr
  ├── 0.zr
  └── 1.zr
```
#### 分块数据（x.zr）
分块的chunk数据

#### 元数据（meta.zr）
包括header与offset两部分

1. header（8B）：全局状态数据
    ```
    const Header = struct { length: u24, chunk_num: u12, compress: enum(u8) { raw = 0, flate = 1 }, pad: u20 };
    ```

2. offset（[]8B）：通过索引表将索引指向实际存储地址来支持高效随机访问，条目是三元组 [chunk_id : u12, offset : u32, physical_length : u20]，长度为N。
    ```
    idx (global)
    ↓
    ↓offset[idx]
    ↓
    chunk_id, offset, physical_length

    const Offset = struct { chunk_id: u12, offset: u32, physical_length: u20 };
    offset: std.ArrayList(Offset)
    ```
    * chunk_id表示具体chunk | offset表示具体chunk内的偏移 | physical_length表示record数据大小 | 隐含：length_max = 16777216（2^24）

### 执行器
负责维护任务队列，工作线程，handle

1. 任务队列：
    * write_task：写任务队列，压入[ops, record]，等待writer弹出
    * read_task：读任务队列，预分配batch并压入[batch, pos, chunk_id, offset, physical_length]，等待reader弹出
        * batch: 具体读取请求下创建的与indices等长的二元组
        * pos：在batch中的位置，保证等序返回
    * gc_task：垃圾回收任务队列，压入batch，等待cleaner弹出

2. 工作线程：执行具体任务的工作线程
    * writer：单线程池执行写任务，固定对应末尾chunk
    * reader：线程池执行读任务
        * num_reader推荐：8-32
    * cleaner：线程池执行垃圾回收任务
        * num_cleaner推荐：2-4

3. handle：
    1. mmap：维护全局chunk文件的handle
        * 初始化阶段注册,关闭前释放
        * 新建chunk：基于ftruncate+mmap实现，一次申请4GiB
        * 仅对于尾chunk使用mmap（读写），其余使用使用mmap+close（只读），一旦写满（writer提交），新建chunk并返回给writer,原mmap close。（避免过多占用fd）
    2. batch：维护每次返回batch的handle,也就是[ptr, logical_length]中ptr的合规性
        * 工作线程完成后注册
        * 必须调用函数来手动释放，释放时batch压入GC队列
    3. sync: 定期向磁盘写入meta.zr来同步数据

#### 在线任务

1. 写任务：写入只允许append-only,其余操作基于offset重定向
    1. 追加：在chunk当前写入位置追加一个record，offset表更新length+1条目，全局长度增加
        * 写满：写入完成时检查，如果chunk大小达到4G, 新建chunk
    2. 修改：追加一个record，并修改offset项
    3. 删除：删除offset项(将目标项替换为最后一项)，length减一（越界访问属于UB行为）

2. 读任务：用一个indices（索引数组），从原数组里访问指定位置的元素(gather),对于python而言是一个NumPy Array
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