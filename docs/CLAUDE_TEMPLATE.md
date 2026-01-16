# CLAUDE.md - 项目指南模板

## 核心理念：内省式探索循环

首要目标是**探索、发现和理解**，而非急于得出结论。

### 探索循环

```
观察 → 提问 → 假设 → 验证 → 反思 → 新问题
```

### 实践原则

- **先理解，后行动**：在写代码前，先理解问题的背景和本质
- **保持好奇心**：每个发现都可能引出新的问题，保持开放的探索态度
- **质疑假设**：主动挑战自己的预设，用数据验证而非确认偏见
- **记录思考过程**：不仅记录"做了什么"，更要记录"为什么这样做"和"发现了什么"
- **拥抱意外**：异常值和意外结果往往是最有价值的发现入口

---

## 工程规范

### 开发流程

```
Notebook 原型开发 → 逻辑验证 → 重构至 src/ 模块化
```

- **Notebook**：用于探索、实验和原型验证
- **src/ 模块**：验证成功的逻辑重构为可复用的 Python 模块
- 避免在 Notebook 中堆积生产代码，保持其轻量和实验性

### 语言约定

- 所有对话、文档和 Notebook 使用中文
- 代码注释使用中文
- Python 代码遵循 PEP 8 风格指南

### 项目目录结构

```text
a190rithm/
├── src/a190rithm/              # 源代码（src-layout）
│   ├── applications/           # 应用场景实现
│   ├── tensorflow/             # TensorFlow 实现
│   ├── torch/                  # PyTorch 实现
│   └── tools/                  # 工具模块
├── tests/                      # 测试代码（镜像 src 结构）
├── notebooks/                  # Jupyter Notebook
├── data/                       # 数据文件（不提交版本控制）
│   ├── raw/                    # 原始数据
│   └── processed/              # 处理后数据
├── docs/                       # 文档
├── scripts/                    # 辅助脚本
└── stubs/                      # 类型存根文件
```

### 命名约定

| 类型 | 规则 | 示例 |
|------|------|------|
| 目录/模块 | snake_case | `data_loader/` |
| Python 文件 | snake_case.py | `model_utils.py` |
| 测试文件 | test_*.py | `test_model_utils.py` |
| Notebook | 序号_描述.ipynb | `01_data_exploration.ipynb` |
| 常量 | UPPER_CASE | `RANDOM_STATE = 42` |

---

## Notebook 规范

### 核心角色：数据叙述者

Notebook 是**讲述数据故事的媒介**。作者应以叙述者身份，引导读者理解：

- 我们在探索什么问题？
- 为什么采用这种方法？
- 数据告诉了我们什么？
- 这些发现意味着什么？

### 结构要求

使用清晰的标题层级组织内容：

- **H1** - Notebook 主题
- **H2** - 主要章节
- **H3** - 章节内子主题

常见的内容组织形式：

| 类型 | 流程 |
|------|------|
| 数据探索 | 加载 → 初探 → 清洗 → EDA → 洞察 |
| 模型实验 | 假设 → 实现 → 训练 → 评估 → 迭代 |
| 算法验证 | 问题定义 → 方案设计 → 实现 → 测试 → 分析 |
| 概念学习 | 理论说明 → 代码演示 → 变体实验 → 总结 |

### 单元格规范

**Markdown 单元格**：

- 代码前说明"做什么"和"为什么"
- 输出后解读"发现了什么"
- 使用过渡语句连接各部分
- 公式使用 LaTeX：行内 `$...$`，独立块 `$$...$$`

**代码单元格**：

- 单个单元格专注一个任务（建议 < 30 行）
- 关键中间结果显式输出
- 耗时操作添加进度提示

### 可复现性

- 固定随机种子
- 使用相对路径
- 记录关键参数
- 确保 Restart & Run All 可执行

### 环境配置参考

```python
# 随机种子
RANDOM_STATE = 42

# 中文显示
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 输出控制
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
pd.set_option('display.max_columns', 20)
```
