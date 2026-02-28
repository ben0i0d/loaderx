# Loaderx
A record-based data runtime, focused on delivering extreme throughput and low latency

**Only Python3.13_Linux_amd64**

## Sampler
Index Generator: a high-performance sampler implemented in Zig

1. Sequential generation: indices are produced by traversing the index space in order.
    * Sliding traversal: indices are obtained using a fixed-size sliding window. Note that in this case, the index space is treated as a circular queue to avoid truncation at the tail.
2. Random generation: indices are sampled randomly from the index space.
    * Global random: a set of samples is drawn randomly from the entire index space.

## Zrecord
基于Zig实现一个并发友好、实现简单、性能更优的 record 存储系统

1. zrecord默认record相互独立，不假定record间存在顺序关系
2. zrecord向Python 侧返回ByteArray，但类型解析由Numpy完成
3. zrecord仅包含一个数据集，长度为 N（N 个 record），所有索引与切块语义等价于 gather 操作
4. zrecord是数据运行时，并不是数据存储引擎，因此将以内存数据为主状态，仅定期持久化到文件系统中
5. 为降低存储体积，支持record级透明压缩，以下是可选的压缩方法
```
| 方法  | 算法    |
| ----- | ------- |
| raw   | 无压缩  | 
| flate | Deflate | 
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
    const Offset = struct { chunk_id: u12, offset: u32, physical_length: u20 };
    offset: std.ArrayList(Offset)
    ```
    * chunk_id表示具体chunk | offset表示具体chunk内的偏移 | physical_length表示record数据大小 | 隐含：length_max = 16777216（2^24）

### 执行器
负责维护任务队列，并安排工作线程

1. 任务队列：
    * write_quene（写任务队列）：压入写任务，等待writer弹出，写入只允许append-only,其余操作基于offset重定向
        1. 追加：在chunk当前写入位置追加一个record，offset表更新length+1条目，全局长度增加
            * 写满：写入完成时检查，如果chunk大小达到4G, 新建chunk
        2. 修改：追加一个record，并修改offset项
        3. 删除：删除offset项(将目标项替换为最后一项)，length减一（越界访问属于UB行为）
    * read_quene（读任务队列）：预分配batch并压入读任务，等待reader弹出
        * 执行顺序：预分配batch → indices（索引数组）解包 → 压入item级读取任务 → reader读取指定位置 → 按照pos（在batch中的位置）组合pyoz.ByteArray
        * 为了并发友好，将batch级解包为item分别压入
        * 由于对python侧保持原地，不再要求zero-copy
    ```
    [idx]
    ↓
    [batch, pos, offset[idx]]
    ↓
    pyoz.ByteArray
    ```
    * gc_quene（垃圾回收任务队列）：压入待释放batch地址，等待cleaner弹出

2. 工作线程：执行具体任务的工作线程
    * writer：单线程执行写任务，固定对应末尾chunk
    * reader：线程池执行读任务
        * num_reader推荐：core  ≤ num_reader ≤ 2*core
    * maintainer：单线程执行垃圾回收/持久化任务（定期向磁盘写入meta.zr来同步数据）

3. mmap：维护chunk文件的handle
    * 初始化阶段注册,关闭前释放
    * 新建chunk：基于ftruncate+mmap实现，一次申请4GiB
    * 仅对于尾chunk使用mmap（读写），其余使用使用mmap+close（只读），一旦写满（writer提交），新建chunk并返回给writer,原mmap close。（避免过多占用fd）

### 分布式扩展
**该部分暂时不会实现，仅提前架构**
1. 分布式下增加了cluster层, node变成一个shard,包含若干个chunk
2. 添加一个indirection表，将全局路径映射到具体node，索引路径变为
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