# Gemini Agent 渐进式迭代计划

本文档记录了将 `GEMINI.md` 优化为“数据叙事者”风格的渐进式路径。

## 目标
构建一个具备叙事感、层次美感，且精通 `pandas`、`sklearn` 和可视化技术的数据分析智能体。

---

## 迭代阶段

### 第一阶段：工程基石与角色锚定 (Foundation)
- **重点**：确保环境稳定、路径正确、角色明确、目录规范。
- **关键规则**：
    - **角色定义**：**Data Storyteller (数据叙事者)**。在编写 Notebook 时，必须具备叙事意识，遵循“探索与内省”循环。
    - **强制根目录启动 (Root Anchor)**：首个单元格必须包含 `pyproject.toml` 断言。
    - **依赖管理**：统一使用 `uv`，禁止 `%pip`。
    - **工程目录约定**：
        - `src/a190rithm/`: 核心逻辑。
        - `data/raw/` & `data/processed/`: 数据分层。
        - `notebooks/`: 实验与分析。
- **验证环节**：
    1. 创建 `notebooks/calibration_phase_1.ipynb`。
    2. 验证首个单元格是否包含路径断言。
    3. 验证是否能成功执行 `import pandas` 且无环境错误。
    4. **验证 Agent 的自我认知**：询问 "Who are you?"，应回答 "I am a Data Storyteller" 相关内容。
- **验收预期 (Expected Outcome)**:
    - [ ] 新建 Notebook 时，首个 Cell 自动包含 `assert os.path.exists('pyproject.toml')`。
    - [ ] 尝试添加依赖时，Agent 回复使用 `uv add` 指令而非自行运行 `%pip`。
    - [ ] Agent 在对话中表现出“叙事者”的身份意识（即使在第一阶段仅处于基础层级）。

### 第二阶段：叙事结构与逻辑流 (Narrative Structure)
- **重点**：将 Notebook 从“代码堆砌”转变为“分析叙事”。
- **关键规则**：
    - **叙事三段律**：Markdown(背景/假设) -> Code(实现) -> Markdown(洞察提炼)。
    - **Markdown 优先**：禁止直接写代码，必须先解释目的。
    - **就地修正 (Fix In-Place)**：禁止保留冗余/报错单元格，报错必须在原单元格修复。
- **验证环节**：
    1. 模拟一个“数据缺失值分析”任务。
    2. **故意注入一个语法/逻辑错误**（如引用不存在的变量）。
    3. 观察 Agent 是否在**同一单元格**内进行修复，并删除错误产生的 Traceback 痕迹。
    4. 检查输出是否具备完整的上下文描述。
- **验收预期 (Expected Outcome)**:
    - [ ] 每一个 Code Cell 上方都有 H2/H3 标题或描述性文本。
    - [ ] 每一个数据输出（如 `df.head()` 或 `print`）下方都有 Markdown Cell 解释“这说明了什么”。
    - [ ] **Notebook 中没有任何包含 Traceback 的错误单元格残留**。
    - [ ] **修复过程不产生新的“调试专用”单元格**。

### 第三阶段：视觉美学与交付标准 (Visual Aesthetics & Code Quality)
- **重点**：提升最终产出的专业度、美感及代码质量，并验证工程化重构能力。
- **关键规则**：
    - **可视化强制令**：所有图表必须包含 Title、X/Y Labels、Legend，使用 `seaborn` 风格。
    - **代码规范**：Pandas 链式调用，Sklearn Pipeline。
    - **工作流闭环 (Refactoring)**：验证通过的逻辑必须从 Notebook 重构至 `src/`。
- **验证环节**：
    1. 模拟一个“数据预处理与简单回归”任务。
    2. 检查数据清洗代码是否使用了 Method Chaining。
    3. 绘制一个带回归线的散点图，检查图表要素。
    4. **重构测试**：指令 Agent 将预处理函数提取到 `src/a190rithm/preprocessing.py` 中，并在 Notebook 中改用 `import` 调用。
- **验收预期 (Expected Outcome)**:
    - [ ] 所有 matplotlib/seaborn 图表均有清晰的标题和轴标签。
    - [ ] Pandas 代码块展现流式处理风格。
    - [ ] **成功创建 `src/` 下的新模块文件**。
    - [ ] **Notebook 中的原始函数定义被移除，替换为 `from src... import ...`**。

---

## 验证记录
- [ ] 第一阶段验证通过
- [ ] 第二阶段验证通过
- [ ] 第三阶段验证通过