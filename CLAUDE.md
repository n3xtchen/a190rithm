# CLAUDE.md

## 项目简介

本项目 `a190rithm` 是一个包含多种深度学习模型实现的集合。主要包括：
- **应用 (Applications)**: 具体应用案例，如 Favorita 杂货销售预测 (Favorita Grocery Sales Forecasting)。
- **模型 (Models)**: 基于 PyTorch 和 TensorFlow 的模型实现（RNN, BERT, GPT2, RoBERTa 等）。

## 代码结构

```text
src/
├── a190rithm/
│   ├── applications/   # 具体应用场景实现
│   ├── tensorflow/     # TensorFlow 相关实现
│   ├── torch/          # PyTorch 模型和工具
│   └── __init__.py
└── __init__.py

tests/                  # 测试代码，按模块划分
└── torch/

data/                   # 数据存储目录（已忽略）
stubs/                  # 类型存根文件
```

**结构说明**: 采用 src-layout 结构。核心逻辑位于 `src/a190rithm`。

## 主要开发命令

- **环境管理**: 使用 `uv` 或标准 pip/virtualenv 管理依赖。
  - 安装依赖: `uv sync` 或 `pip install -e .`
- **运行测试**:
  - 运行所有测试: `pytest`

## 高层架构要点

- **多框架支持**: 同时包含 PyTorch (`src/a190rithm/torch`) 和 TensorFlow (`src/a190rithm/tensorflow`) 的实现。
- **依赖管理**: 项目依赖定义在 `pyproject.toml` 中，包含 `pandas`, `pyarrow` 等核心库。
- **类型检查**: 配置了 `pyright` 进行类型检查，存根文件位于 `stubs/`。

## 代码规范

- 使用 Python 3.10+。
- 遵循 PEP 8 风格。
- 提交前请确保测试通过。
