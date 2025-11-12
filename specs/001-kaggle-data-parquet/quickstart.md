# Kaggle 数据下载与 Parquet 转换 - 快速入门指南

本指南将帮助你快速上手使用 Kaggle 数据下载与 Parquet 格式转换工具。该工具允许你从 Kaggle 平台下载数据集并将其转换为高效的 Parquet 格式，便于数据科学和机器学习项目使用。

## 目录

1. [安装](#安装)
2. [配置](#配置)
3. [基本用法](#基本用法)
4. [高级用法](#高级用法)
5. [常见问题与解决方案](#常见问题与解决方案)

## 安装

### 依赖项

确保你的系统上已安装 Python 3.8 或更高版本。

### 通过 pip 安装

```bash
pip install a190rithm
```

### 从源码安装

```bash
git clone https://github.com/user/a190rithm.git
cd a190rithm
pip install -e .
```

## 配置

### 获取 Kaggle API 凭证

要使用 Kaggle API，你需要获取 API 凭证：

1. 登录你的 [Kaggle 账号](https://www.kaggle.com/)
2. 访问 "Account" 页面，点击 "Create New API Token"
3. 下载 `kaggle.json` 文件，其中包含 API 凭证

### 设置凭证

有多种方法可以设置你的 Kaggle API 凭证：

#### 方法 1: 环境变量

```bash
export KAGGLE_USERNAME=your_username
export KAGGLE_KEY=your_key
```

#### 方法 2: 配置文件

使用交互式配置命令：

```bash
kaggle-parquet config --set-kaggle-credentials
```

或者手动编辑配置文件（默认位于 `~/.kaggle-parquet/config.yml`）：

```yaml
kaggle:
  username: your_username
  key: your_key
```

#### 方法 3: 直接传递参数

在使用命令行或 Python API 时直接传递凭证参数（不推荐）：

```bash
kaggle-parquet download username/dataset-name --kaggle-username your_username --kaggle-key your_key
```

## 基本用法

### 命令行界面

#### 下载并转换数据集

```bash
# 下载数据集并自动转换为 Parquet 格式
kaggle-parquet download username/dataset-name

# 下载数据集但不转换
kaggle-parquet download username/dataset-name --no-convert

# 指定输出目录
kaggle-parquet download username/dataset-name --output-dir ./my_data
```

#### 转换已下载的数据

```bash
# 转换单个文件
kaggle-parquet convert data.csv

# 转换目录中的所有文件
kaggle-parquet convert ./data_dir --recursive

# 使用特定压缩算法
kaggle-parquet convert data.csv --compression zstd
```

#### 查看已下载的数据集

```bash
# 列出所有已下载的数据集
kaggle-parquet list

# 显示详细信息
kaggle-parquet list --detail

# 以 JSON 格式输出
kaggle-parquet list --format json
```

### Python API

#### 简单用法

```python
from a190rithm.applications.kaggle_downloader import download_and_convert

# 下载并转换
dataset, parquet_files = download_and_convert("username/dataset-name")

# 查看结果
print(f"下载的文件: {len(dataset.files)}")
print(f"转换的 Parquet 文件: {len(parquet_files)}")
```

#### 使用客户端类

```python
from a190rithm.applications.kaggle_downloader import KaggleClient, DataConverter

# 初始化客户端
client = KaggleClient()

# 搜索数据集
datasets = client.search_datasets("covid data")
for ds in datasets[:3]:
    print(f"{ds['ref']}: {ds['title']} ({ds['size']})")

# 下载选定的数据集
dataset = client.download_dataset(datasets[0]['ref'])

# 转换为 Parquet
converter = DataConverter()
parquet_files = converter.convert_dataset(dataset)
```

## 高级用法

### 按列分区数据

分区可以提高查询效率，特别是对于大型数据集：

```bash
kaggle-parquet convert large_data.csv --partition-by year,month
```

```python
from a190rithm.applications.kaggle_downloader import DataConverter

converter = DataConverter()
parquet_files = converter.convert_file("large_data.csv", partition_by=["year", "month"])
```

### 处理大型数据集

对于接近或超过内存大小的数据集：

```bash
kaggle-parquet convert huge_data.csv --chunk-size 50000 --processes 4
```

```python
from a190rithm.applications.kaggle_downloader import DataConverter

converter = DataConverter(chunk_size=50000, processes=4)
parquet_files = converter.convert_file("huge_data.csv")
```

### 自定义存储结构

自定义数据集的存储结构：

```python
from a190rithm.applications.kaggle_downloader import StorageManager, KaggleClient

# 自定义存储结构
storage = StorageManager(
    base_dir="./datasets",
    structure_template="kaggle/{owner}/{name}/{version}"
)

client = KaggleClient()
dataset = client.download_dataset("username/dataset-name")

# 获取自定义路径
path = storage.get_dataset_path(dataset)
print(f"数据集存储在: {path}")
```

### 错误处理

```python
from a190rithm.applications.kaggle_downloader import (
    download_and_convert,
    KaggleAPIError,
    DownloadError,
    ConversionError
)

try:
    dataset, parquet_files = download_and_convert("username/dataset-name")
except KaggleAPIError as e:
    print(f"Kaggle API 错误: {e}")
except DownloadError as e:
    print(f"下载错误: {e}")
except ConversionError as e:
    print(f"转换错误: {e}")
```

## 常见问题与解决方案

### 认证问题

**问题**: 出现 "Unauthorized" 或 "Authentication failed" 错误。

**解决方案**:
1. 确认你的 Kaggle API 凭证是否有效
2. 检查环境变量是否正确设置
3. 使用 `kaggle-parquet config --set-kaggle-credentials` 重新配置

### 大文件处理

**问题**: 处理大文件时内存不足。

**解决方案**:
1. 减小 `chunk-size` 参数值
2. 增加系统虚拟内存
3. 使用支持分布式处理的功能（未来计划）

### 转换失败

**问题**: 特定格式文件转换失败。

**解决方案**:
1. 检查文件是否损坏或格式不正确
2. 使用 `--verbose` 查看详细错误信息
3. 对于特殊格式，尝试先转换为 CSV，再转换为 Parquet

### 网络问题

**问题**: 下载大型数据集时网络连接中断。

**解决方案**:
1. 增加 `--retries` 参数值
2. 使用更稳定的网络连接
3. 利用 `--force` 参数继续未完成的下载

## 下一步

- 查看 [完整文档](https://github.com/user/a190rithm/docs)
- 参与 [项目开发](https://github.com/user/a190rithm)
- 报告 [问题或建议](https://github.com/user/a190rithm/issues)