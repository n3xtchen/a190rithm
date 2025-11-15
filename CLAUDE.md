# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介

本项目用于学习和实践深度学习模型。项目整体以促进理解和应用相关模型为目标，部分功能尚处于规划或开发阶段。

## 代码结构

- src/a19rithm
  - applications: 代码应用
    - data_loader.py
    - model.py

## 主要开发命令

- 依赖安装和环境准备：根据各模块说明安装 Python/Scala 等环境及依赖（README 未明示具体命令）。
- 运行与测试：具体执行方式依赖于每个模型和脚本实现，请参考代码文件和注释进行对应操作。
- 若涉及 wandb、通用执行器、数据集测试下载等功能，参见对应源码与 TODO 标记部分。

## 高层架构要点

- 以 Keras 实现深度学习相关模型，数据及脚本分布在各自目录下。
- 使用 numpy、pandas、scipy 和 scikit-learn 进行特征处理
- 数据及模型相关产物规避入库，已在 .gitignore 忽略 data/ 与 stubs/ 目录。

## 参考

- 为获取更多项目结构信息、API 流程及实现细节，建议直接阅读源码、各算法实现及对应目录下的注释说明。

## Active Technologies
- 文件系统 (数据存储在本地data目录) (001-kaggle-data-parquet)
- Python 3.8+ (001-kaggle-data-parquet)

## Recent Changes
- 001-kaggle-data-parquet: Added 文件系统 (数据存储在本地data目录)
