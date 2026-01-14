# Agent 工作流与操作规范 (Workflow Guidelines)

## 变更记录 (Change Log)

| 日期 | 版本 | 变更内容 | 备注 |
| :--- | :--- | :--- | :--- |
| 2026-01-14 | v1.3 | 统一路径与启动目录规范 | 明确 Kernel 必须在项目根目录启动，并与静态项目结构规范对齐。 |
| 2026-01-14 | v1.2 | 重构项目目录展示 | 使用目录树展示项目结构，强化 Python 通用规范。 |
| 2026-01-14 | v1.1 | 文档架构重构 | 将项目管理提升为通用规范，Notebook 降级为子规范。 |
| 2026-01-14 | v1.0 | 初始创建 | 基于 Jupyter MCP Server 分析报告迭代。 |

---

本文档旨在记录和维护在本项目中的最佳实践与操作规范，以提高协作效率和稳定性。

## 1. Python 项目通用规范 (General Python Standards)

### 1.1 项目结构 (Project Directory Tree)

```text
a190rithm/
├── pyproject.toml          # 项目配置文件 (Dependency, Build, Lint)
├── uv.lock                 # 依赖锁定文件 (使用 uv 管理)
├── src/                    # 源代码目录 (Python Project Standard)
│   └── a190rithm/          # 核心逻辑模块
│       ├── applications/   # 特定任务/应用实现
│       ├── tensorflow/     # TF 相关工具与模型
│       ├── torch/          # PyTorch 相关工具与模型
│       └── tools/          # 通用工具类 (如 Kaggle 下载器)
├── data/                   # 数据存储目录
├── notebooks/              # 研究与 EDA (使用 Jupyter Notebook)
├── docs/                   # 项目文档
│   └── agent/              # Agent 协作分析报告、日志及规范
└── tests/                  # 单元测试与集成测试
```

**原则**: 核心逻辑必须封装在 `src/a190rithm/` 中。Notebook 仅通过 `import` 调用核心逻辑。

### 1.2 环境与依赖管理 (Environment)

*   **工具**: 本项目统一使用 **`uv`** 进行环境管理。
*   **依赖安装**:
    *   必须使用外部 Shell 工具执行安装：`uv pip install <package>`。
*   **❌ 禁止事项**: 严禁在任何脚本或 Notebook 单元格中通过 Magic Command (`%pip`) 安装依赖。

## 2. Jupyter Notebook 操作子规范 (Notebook Sub-Standards)

### 2.1 启动目录规范 (Working Directory Policy)
*   **强制规定**: 所有 Notebook Kernel 必须在 **项目根目录 (`a190rithm/`)** 启动。
*   **目的**: 确保运行时环境与项目目录树规范完全匹配，无需使用相对路径处理数据读取。
*   **验证动作**: 在 Notebook 初始化单元格中进行断言校验。
    ```python
    import os
    # 断言当前工作目录是项目根目录（包含 pyproject.toml）
    assert os.path.exists('pyproject.toml'), f"错误：Kernel 未在项目根目录启动。当前目录: {os.getcwd()}"
    ```

### 2.2 运行时依赖 (Runtime Dependencies)
*   **Kernel 重启**: 安装新库后，必须调用 `restart_notebook` 工具，否则新库无法在内存中加载。

### 2.3 效率与 Token 管理 (Efficiency)
*   **策略性读取**: 优先使用 `response_format='brief'` 调用 `read_notebook`。
*   **减少富媒体输出**: 除非必要，避免产生超大型的 Base64 图像输出，以免填满 Context Window。

### 2.4 单元格 (Cell) 维护
*   **索引偏移风险**: 单元格 Index 在 `insert` / `delete` 后会动态变化。进行连续修改前，务必重新读取 Notebook结构。
*   **初始化逻辑**: 确保头部有 Initialization Cell（Imports, Assertion Check），以便在 `restart_notebook` 后能快速恢复状态。
