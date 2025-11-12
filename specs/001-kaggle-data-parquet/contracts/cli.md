# CLI 接口规范

## 概述

`kaggle-parquet` 命令行工具允许用户从 Kaggle 平台下载数据集并将其转换为 Parquet 格式。本文档定义了命令行接口的使用方式、参数和选项。

## 命令行结构

```
kaggle-parquet [OPTIONS] COMMAND [ARGS]...
```

### 全局选项

| 选项 | 短选项 | 默认值 | 描述 |
|------|-------|--------|------|
| `--log-level` | `-l` | `INFO` | 设置日志级别 (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `--config` | `-c` | `~/.kaggle-parquet/config.yml` | 指定配置文件路径 |
| `--output-dir` | `-o` | `./data` | 指定数据输出目录 |
| `--verbose` | `-v` | `False` | 启用详细输出模式 |
| `--quiet` | `-q` | `False` | 静默模式，只显示错误信息 |
| `--help` | `-h` | - | 显示帮助信息 |
| `--version` | - | - | 显示版本信息 |

## 命令

### `download`

从 Kaggle 下载数据集。

```
kaggle-parquet download DATASET_ID [OPTIONS]
```

#### 参数

- `DATASET_ID`: Kaggle 数据集标识符，格式为 `username/dataset-name`

#### 选项

| 选项 | 短选项 | 默认值 | 描述 |
|------|-------|--------|------|
| `--no-convert` | - | `False` | 仅下载数据集，不进行 Parquet 转换 |
| `--force` | `-f` | `False` | 覆盖已存在的文件 |
| `--limit` | - | `None` | 限制下载的文件数量 |
| `--include` | - | `None` | 包含的文件类型，多个类型用逗号分隔 (例如 `csv,json`) |
| `--exclude` | - | `None` | 排除的文件类型，多个类型用逗号分隔 |
| `--timeout` | - | `600` | 下载超时时间（秒） |
| `--retries` | - | `3` | 下载失败重试次数 |
| `--concurrent` | - | `2` | 并发下载文件数量 |

### `convert`

将已下载的数据文件转换为 Parquet 格式。

```
kaggle-parquet convert PATH [OPTIONS]
```

#### 参数

- `PATH`: 数据文件或目录路径

#### 选项

| 选项 | 短选项 | 默认值 | 描述 |
|------|-------|--------|------|
| `--recursive` | `-r` | `False` | 递归处理子目录 |
| `--force` | `-f` | `False` | 覆盖已存在的 Parquet 文件 |
| `--compression` | - | `snappy` | Parquet 压缩算法 (`none`, `snappy`, `gzip`, `brotli`, `lz4`, `zstd`) |
| `--chunk-size` | - | `100000` | 处理大文件时的分块大小（行数） |
| `--preserve-index` | - | `False` | 保留原始数据索引 |
| `--partition-by` | - | `None` | 按指定列分区 (例如 `year,month`) |
| `--row-group-size` | - | `100000` | Parquet 行组大小 |
| `--processes` | `-p` | `CPU核心数` | 并行处理使用的进程数 |

### `config`

管理配置设置。

```
kaggle-parquet config [OPTIONS] [KEY] [VALUE]
```

#### 参数

- `KEY`: 配置键名
- `VALUE`: 配置值

#### 选项

| 选项 | 短选项 | 默认值 | 描述 |
|------|-------|--------|------|
| `--list` | `-l` | - | 列出当前配置 |
| `--reset` | - | `False` | 重置为默认配置 |
| `--set-kaggle-credentials` | - | - | 交互式设置 Kaggle API 凭据 |

### `list`

列出已下载的数据集。

```
kaggle-parquet list [OPTIONS]
```

#### 选项

| 选项 | 短选项 | 默认值 | 描述 |
|------|-------|--------|------|
| `--detail` | `-d` | `False` | 显示详细信息 |
| `--format` | - | `table` | 输出格式 (`table`, `json`, `csv`) |
| `--filter` | - | `None` | 按属性过滤 (例如 `name=iris`) |

## 退出状态码

- `0`: 成功
- `1`: 一般错误
- `2`: 命令行参数错误
- `3`: Kaggle API 错误
- `4`: 网络错误
- `5`: 转换错误
- `6`: 文件系统错误

## 环境变量

- `KAGGLE_USERNAME`: Kaggle 用户名
- `KAGGLE_KEY`: Kaggle API 密钥
- `KAGGLE_PARQUET_CONFIG_PATH`: 配置文件路径
- `KAGGLE_PARQUET_OUTPUT_DIR`: 数据输出目录

## 配置文件格式

配置文件使用 YAML 格式：

```yaml
# ~/.kaggle-parquet/config.yml

# Kaggle API 设置
kaggle:
  username: ${KAGGLE_USERNAME}
  key: ${KAGGLE_KEY}

# 下载设置
download:
  timeout: 600
  retries: 3
  concurrent: 2

# 转换设置
convert:
  compression: snappy
  chunk_size: 100000
  row_group_size: 100000
  processes: 4

# 输出设置
output:
  dir: ./data
  structure: "kaggle/{dataset_name}_{timestamp}"

# 日志设置
logging:
  level: INFO
  file: ~/.kaggle-parquet/logs/kaggle-parquet.log
  rotation: 5MB
  max_files: 3
```