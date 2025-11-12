# 数据模型: Kaggle 数据下载与 Parquet 格式转换

## 概述

本文档定义了 Kaggle 数据下载与 Parquet 格式转换功能所涉及的关键数据实体、属性和关系。这些模型将用于实现系统中的数据结构和操作流程。

## 核心实体

### Dataset

表示 Kaggle 上的数据集。

| 属性 | 类型 | 描述 | 验证规则 |
|------|------|------|---------|
| id | str | 数据集在 Kaggle 平台上的唯一标识符 | 非空，格式为 "username/dataset-name" |
| name | str | 数据集名称 | 非空 |
| owner | str | 数据集创建者/所有者 | 非空 |
| url | str | 数据集在 Kaggle 平台的 URL | 有效的 URL 格式 |
| size | int | 数据集大小（字节） | ≥ 0，≤ 10GB (10,737,418,240 字节) |
| timestamp | datetime | 下载时间戳 | ISO 8601 格式 |
| description | str | 数据集描述信息 | 可选 |
| files | List[DataFile] | 数据集包含的文件列表 | 至少一个文件 |
| metadata | Dict | 其他元数据信息 | 可选 |
| status | DatasetStatus | 数据集处理状态 | 有效的枚举值 |

### DataFile

表示数据集中的单个数据文件。

| 属性 | 类型 | 描述 | 验证规则 |
|------|------|------|---------|
| filename | str | 文件名称 | 非空，有效的文件名格式 |
| format | FileFormat | 文件格式 | 有效的枚举值 |
| size | int | 文件大小（字节） | ≥ 0 |
| path | str | 本地存储路径 | 非空，有效路径格式 |
| columns | List[str] | 数据列名称（表格数据） | 可选 |
| schema | Dict | 数据架构 | 可选 |
| download_status | DownloadStatus | 下载状态 | 有效的枚举值 |
| download_progress | float | 下载进度（0-100） | 0 ≤ 值 ≤ 100 |
| checksum | str | 文件校验和（用于验证完整性） | 可选，MD5 或 SHA-256 格式 |

### ParquetFile

表示转换后的 Parquet 格式文件。

| 属性 | 类型 | 描述 | 验证规则 |
|------|------|------|---------|
| original_file | DataFile | 对应的原始数据文件 | 必须是有效的 DataFile 实例 |
| filename | str | Parquet 文件名称 | 非空，以 ".parquet" 结尾 |
| path | str | 存储路径 | 非空，有效路径格式 |
| size | int | 文件大小（字节） | ≥ 0 |
| schema | Dict | Parquet 架构 | 非空 |
| rows | int | 数据行数 | ≥ 0 |
| compression_ratio | float | 相对原始文件的压缩比 | > 0 |
| partition_cols | List[str] | 分区列（如果适用） | 可选 |
| timestamp | datetime | 转换时间戳 | ISO 8601 格式 |
| conversion_status | ConversionStatus | 转换状态 | 有效的枚举值 |

## 枚举类型

### DatasetStatus

表示数据集处理的当前状态。

- `PENDING`: 等待处理
- `DOWNLOADING`: 正在下载
- `DOWNLOADED`: 下载完成
- `CONVERTING`: 正在转换为 Parquet
- `COMPLETED`: 处理完成
- `FAILED`: 处理失败

### DownloadStatus

表示单个文件下载的状态。

- `PENDING`: 等待下载
- `IN_PROGRESS`: 正在下载
- `COMPLETED`: 下载完成
- `FAILED`: 下载失败
- `SKIPPED`: 已跳过（如文件已存在）

### ConversionStatus

表示 Parquet 转换的状态。

- `PENDING`: 等待转换
- `IN_PROGRESS`: 正在转换
- `COMPLETED`: 转换完成
- `FAILED`: 转换失败
- `UNSUPPORTED`: 不支持转换（不兼容的文件格式）

### FileFormat

支持转换的文件格式。

- `CSV`: CSV 文件
- `JSON`: JSON 文件
- `EXCEL`: Excel 文件 (.xls, .xlsx)
- `TSV`: Tab 分隔值文件
- `PARQUET`: 已经是 Parquet 格式
- `AVRO`: Avro 格式
- `ORC`: ORC 格式
- `XML`: XML 文件
- `HTML`: HTML 文件
- `TXT`: 文本文件
- `OTHER`: 其他格式（可能不支持转换）

## 状态转换

数据集处理涉及以下状态转换流程：

1. PENDING → DOWNLOADING: 开始下载数据集文件
2. DOWNLOADING → DOWNLOADED: 所有文件下载完成
3. DOWNLOADING → FAILED: 下载过程失败
4. DOWNLOADED → CONVERTING: 开始转换为 Parquet 格式
5. CONVERTING → COMPLETED: 所有文件转换完成
6. CONVERTING → FAILED: 转换过程失败

## 数据存储结构

数据将按照以下结构存储在 `data` 目录中：

```
data/
└── kaggle/
    └── {dataset_name}_{timestamp}/
        ├── original/
        │   ├── file1.csv
        │   └── file2.json
        ├── parquet/
        │   ├── file1.parquet
        │   └── file2.parquet
        └── metadata.json
```

`metadata.json` 文件包含数据集的完整元数据，包括所有文件的信息、处理状态、时间戳等。