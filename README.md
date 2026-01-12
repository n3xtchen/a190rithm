# 机器学习与深度学习模型的学习与实践

## 介绍

这是一个用于学习和实践机器学习与深度学习模型的项目。项目包含了多种经典算法的实现，旨在帮助用户理解和应用这些算法。

## 功能

### 易用性

- 通用执行器 <todo>
- 整合 wandb <todo>
- 代码配置化 <todo>

### dataset

- Kaggle 数据集下载与 Parquet 自动转换工具 (kaggle-parquet)
- 测试数据集下载 <todo>

### 模型

#### Pytorch

- Bert 文本分类器
  - 二分类
  - 多分类 <todo>
- gpt 文本分类器 <todo>

#### Scala(删除)

删除原因呢：scala 还是专注在数据处理层面

- 关联规则学习（Association rule ）
  - Apriori
  - FP Growth
- 梯度下降（Gradient Descent）<pending>
  - 批量梯度下降（BGD，Batch Gradient Descent）
  - 随机梯度下降（SGD, Stochastic Gradient Descent）
  - 小批量梯度下降（MBGD, Mini Batch Gradient Descent）
  - 动量（Momentum）

## Kaggle 数据下载与转换工具 (kaggle-parquet)

该项目包含一个专门用于从 Kaggle 下载数据集并将其自动转换为 Parquet 格式的工具，特别针对大型数据集（如 GB 级别）进行了优化。

### 主要功能
- **自动化下载**：从 Kaggle 下载数据集并自动解压。
- **高效转换**：使用 `pyarrow` 将 CSV/JSON/Excel 转换为 Parquet 格式，支持大文件分块处理和多进程并行转换。
- **元数据管理**：自动保存数据集元数据和转换统计信息。

### 使用方法

所有命令建议通过 `uv run` 执行：

#### 1. 配置 Kaggle 凭证
在第一次使用前，建议设置 Kaggle API 凭证：
```bash
uv run kaggle-parquet config --set-kaggle-credentials
```
或者设置环境变量 `KAGGLE_USERNAME` 和 `KAGGLE_KEY`。

#### 2. 下载并转换数据集
下载指定数据集并自动执行 Parquet 转换：
```bash
uv run kaggle-parquet download ruiyuanfan/corporacin-favorita-grocery-sales-forecasting
```

#### 3. 仅转换本地文件
如果你已经有了本地 CSV 文件，可以手动触发转换：
```bash
uv run kaggle-parquet convert ./path/to/your/csv_files --recursive
```

#### 4. 查看已下载的数据集
```bash
uv run kaggle-parquet list
```

## 环境配置

```
uv sync --all-groups
uv pip install -e .
```

启动 jupyter lab 并开启 jupyter mcp server extension，允许部分 notebook mcp tool

```bash
jupyter lab --port 4040 --IdentityProvider.token MY_TOKEN --JupyterMCPServerExtensionApp.allowed_jupyter_mcp_tools="notebook_run-all-cells,notebook_get-selected-cell,notebook_append-execute"
```
