"""
Kaggle 数据下载与 Parquet 格式转换工具的主入口模块

允许通过 python -m a190rithm.tools.kaggle_downloader 运行工具。
"""

import sys
from .cli import main


if __name__ == "__main__":
    sys.exit(main())