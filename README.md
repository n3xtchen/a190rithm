# 机器学习与深度学习模型的学习与实践

## 介绍

这是一个用于学习和实践机器学习与深度学习模型的项目。项目包含了多种经典算法的实现，旨在帮助用户理解和应用这些算法。

## 功能

### 易用性

- 通用执行器 <todo>
- 整合 wandb <todo>
- 代码配置化 <todo>

### dataset

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

## 环境配置

启动 jupyter lab 并开启 jupyter mcp server extension，允许部分 notebook mcp tool

```bash
jupyter lab --port 4040 --IdentityProvider.token MY_TOKEN --JupyterMCPServerExtensionApp.allowed_jupyter_mcp_tools="notebook_run-all-cells,notebook_get-selected-cell,notebook_append-execute"
```
