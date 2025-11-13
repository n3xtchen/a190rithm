"""
命令行接口模块

提供 kaggle-parquet 命令行工具的实现，允许通过命令行下载和转换 Kaggle 数据集。
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__


def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器。

    返回:
        argparse.ArgumentParser: 配置好的参数解析器
    """
    parser = argparse.ArgumentParser(
        prog="kaggle-parquet",
        description="从 Kaggle 下载数据集并转换为 Parquet 格式",
        epilog="了解更多信息，请访问 https://github.com/user/a190rithm"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="设置日志级别 (默认: INFO)"
    )
    parser.add_argument(
        "--config", "-c",
        default="~/.kaggle-parquet/config.yml",
        help="指定配置文件路径 (默认: ~/.kaggle-parquet/config.yml)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./data",
        help="指定数据输出目录 (默认: ./data)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细输出模式"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，只显示错误信息"
    )

    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # download 子命令
    download_parser = subparsers.add_parser(
        "download",
        help="从 Kaggle 下载数据集"
    )
    download_parser.add_argument(
        "dataset_id",
        help="Kaggle 数据集标识符，格式为 'username/dataset-name'"
    )
    download_parser.add_argument(
        "--no-convert",
        action="store_true",
        help="仅下载数据集，不进行 Parquet 转换"
    )
    download_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="覆盖已存在的文件"
    )
    download_parser.add_argument(
        "--limit",
        type=int,
        help="限制下载的文件数量"
    )
    download_parser.add_argument(
        "--include",
        help="包含的文件类型，多个类型用逗号分隔 (例如 'csv,json')"
    )
    download_parser.add_argument(
        "--exclude",
        help="排除的文件类型，多个类型用逗号分隔"
    )
    download_parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="下载超时时间（秒）(默认: 600)"
    )
    download_parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="下载失败重试次数 (默认: 3)"
    )
    download_parser.add_argument(
        "--concurrent",
        type=int,
        default=2,
        help="并发下载文件数量 (默认: 2)"
    )

    # convert 子命令
    convert_parser = subparsers.add_parser(
        "convert",
        help="将已下载的数据文件转换为 Parquet 格式"
    )
    convert_parser.add_argument(
        "path",
        help="数据文件或目录路径"
    )
    convert_parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="递归处理子目录"
    )
    convert_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="覆盖已存在的 Parquet 文件"
    )
    convert_parser.add_argument(
        "--compression",
        choices=["none", "snappy", "gzip", "brotli", "lz4", "zstd"],
        default="snappy",
        help="Parquet 压缩算法 (默认: snappy)"
    )
    convert_parser.add_argument(
        "--chunk-size",
        type=int,
        default=100000,
        help="处理大文件时的分块大小（行数）(默认: 100000)"
    )
    convert_parser.add_argument(
        "--preserve-index",
        action="store_true",
        help="保留原始数据索引"
    )
    convert_parser.add_argument(
        "--partition-by",
        help="按指定列分区 (例如 'year,month')"
    )
    convert_parser.add_argument(
        "--row-group-size",
        type=int,
        default=100000,
        help="Parquet 行组大小 (默认: 100000)"
    )
    convert_parser.add_argument(
        "--processes", "-p",
        type=int,
        help="并行处理使用的进程数 (默认: CPU核心数)"
    )

    # config 子命令
    config_parser = subparsers.add_parser(
        "config",
        help="管理配置设置"
    )
    config_parser.add_argument(
        "key",
        nargs="?",
        help="配置键名"
    )
    config_parser.add_argument(
        "value",
        nargs="?",
        help="配置值"
    )
    config_parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出当前配置"
    )
    config_parser.add_argument(
        "--reset",
        action="store_true",
        help="重置为默认配置"
    )
    config_parser.add_argument(
        "--set-kaggle-credentials",
        action="store_true",
        help="交互式设置 Kaggle API 凭据"
    )
    config_parser.add_argument(
        "--use-keyring",
        action="store_true",
        help="使用系统密钥环存储凭据"
    )

    # list 子命令
    list_parser = subparsers.add_parser(
        "list",
        help="列出已下载的数据集"
    )
    list_parser.add_argument(
        "--detail", "-d",
        action="store_true",
        help="显示详细信息"
    )
    list_parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="输出格式 (默认: table)"
    )
    list_parser.add_argument(
        "--filter",
        help="按属性过滤 (例如 'name=iris')"
    )

    return parser


def handle_download(args: argparse.Namespace) -> int:
    """
    处理 download 子命令。

    参数:
        args: 命令行参数

    返回:
        int: 退出状态码
    """
    from .kaggle_client import KaggleClient
    from .download_tracker import DownloadTracker
    from .exceptions import (
        AuthenticationError, DatasetNotFoundError,
        DownloadError, KaggleAPIError
    )
    from .utils.logging_utils import setup_logging

    # 设置日志级别
    if args.verbose:
        setup_logging(level="DEBUG")
    elif args.quiet:
        setup_logging(level="WARNING")
    else:
        setup_logging(level=args.log_level)

    # 解析包含/排除文件参数
    include_files = args.include.split(",") if args.include else None
    exclude_files = args.exclude.split(",") if args.exclude else None

    try:
        # 创建 Kaggle 客户端
        client = KaggleClient(
            timeout=args.timeout,
            max_retries=args.retries
        )

        # 验证凭证
        if not client.verify_credentials():
            print("错误: Kaggle API 凭证无效，请设置有效的凭证")
            print("可以使用以下方式设置凭证:")
            print("1. 运行 'kaggle-parquet config --set-kaggle-credentials'")
            print("2. 设置环境变量 KAGGLE_USERNAME 和 KAGGLE_KEY")
            print("3. 编辑 ~/.kaggle-parquet/config.yml 文件")
            return 3

        # 下载数据集
        print(f"下载数据集: {args.dataset_id}")
        print(f"目标目录: {args.output_dir or client.config.get('output.dir')}")

        dataset = client.download_dataset(
            dataset_id=args.dataset_id,
            path=args.output_dir,
            force=args.force,
            quiet=args.quiet,
            include_files=include_files,
            exclude_files=exclude_files
        )

        # 创建下载跟踪器并完成下载
        tracker = DownloadTracker(dataset.files[0].path.rsplit("/original", 1)[0])
        tracker.complete_download(dataset)

        print(f"数据集下载完成: {dataset.id}")
        print(f"  - 文件数量: {len(dataset.files)}")
        print(f"  - 总大小: {dataset.size / 1024 / 1024:.2f} MB")

        # 如果不需要转换，直接返回
        if args.no_convert:
            print("跳过转换，下载过程已完成")
            return 0

        # 否则继续转换
        print("开始转换文件为 Parquet 格式...")
        # 这里调用转换逻辑，暂时只打印信息
        print("转换功能将在后续实现")

        return 0

    except AuthenticationError as e:
        print(f"认证错误: {e}")
        return 3
    except DatasetNotFoundError as e:
        print(f"数据集不存在: {e}")
        return 1
    except DownloadError as e:
        print(f"下载错误: {e}")
        return 4
    except KaggleAPIError as e:
        print(f"Kaggle API 错误: {e}")
        return 3
    except Exception as e:
        print(f"未知错误: {e}")
        return 1


def handle_convert(args: argparse.Namespace) -> int:
    """
    处理 convert 子命令。

    参数:
        args: 命令行参数

    返回:
        int: 退出状态码
    """
    # 将在实现功能后完成
    print(f"转换数据: {args.path}")
    return 0


def handle_config(args: argparse.Namespace) -> int:
    """
    处理 config 子命令。

    参数:
        args: 命令行参数

    返回:
        int: 退出状态码
    """
    import getpass
    import keyring
    import tabulate
    from .config import Config
    from .utils.logging_utils import setup_logging

    # 设置日志级别
    if args.verbose:
        setup_logging(level="DEBUG")
    elif args.quiet:
        setup_logging(level="WARNING")
    else:
        setup_logging(level=args.log_level)

    # 创建配置对象
    config = Config(args.config)

    if args.list:
        # 列出所有配置
        configs = []
        for section in ["kaggle", "download", "convert", "output", "logging", "security"]:
            for key, value in _get_nested_config(config, section).items():
                configs.append([f"{section}.{key}", str(value)])

        # 以表格形式输出
        print(tabulate.tabulate(configs, headers=["配置项", "值"], tablefmt="psql"))
        return 0

    elif args.reset:
        # 重置配置
        config.reset()
        print("配置已重置为默认值")
        return 0

    elif args.set_kaggle_credentials:
        # 交互式设置 Kaggle 凭据
        print("设置 Kaggle API 凭据")
        print("请在 Kaggle 网站上创建 API 令牌: https://www.kaggle.com/settings")
        print()

        username = input("Kaggle 用户名: ").strip()
        key = getpass.getpass("Kaggle API 密钥: ").strip()

        if not username or not key:
            print("错误: 用户名和密钥不能为空")
            return 1

        # 保存凭据
        if args.use_keyring:
            try:
                keyring.set_password("kaggle-parquet", "username", username)
                keyring.set_password("kaggle-parquet", "key", key)
                print("凭据已保存到系统密钥环")
            except Exception as e:
                print(f"保存到密钥环失败: {e}")
                print("尝试保存到配置文件...")
                config.set("kaggle.username", username)
                config.set("kaggle.key", key)
                print("凭据已保存到配置文件")
        else:
            config.set("kaggle.username", username)
            config.set("kaggle.key", key)
            print("凭据已保存到配置文件")

        # 确保设置了使用密钥环的配置
        config.set("security.use_keyring", args.use_keyring)
        return 0

    elif args.key and args.value is not None:
        # 设置指定配置项
        config.set(args.key, args.value)
        print(f"已设置配置 {args.key}={args.value}")
        return 0

    elif args.key:
        # 获取指定配置项
        value = config.get(args.key)
        if value is None:
            print(f"配置项 {args.key} 不存在")
            return 1
        print(f"{args.key}={value}")
        return 0

    else:
        print("请指定操作或使用 --help 查看帮助")
        return 0


def _get_nested_config(config: 'Config', section: str) -> dict:
    """获取嵌套的配置部分"""
    result = {}
    section_dict = config.config.get(section, {})
    for key, value in section_dict.items():
        result[key] = value
    return result


def handle_list(args: argparse.Namespace) -> int:
    """
    处理 list 子命令。

    参数:
        args: 命令行参数

    返回:
        int: 退出状态码
    """
    import glob
    import json
    import os
    from pathlib import Path
    import tabulate
    import csv
    import sys

    from .config import Config
    from .utils.logging_utils import setup_logging

    # 设置日志级别
    if args.verbose:
        setup_logging(level="DEBUG")
    elif args.quiet:
        setup_logging(level="WARNING")
    else:
        setup_logging(level=args.log_level)

    # 获取数据目录
    config = Config(args.config)
    base_dir = os.path.expanduser(config.get("output.dir", "./data"))
    kaggle_dir = os.path.join(base_dir, "kaggle")

    if not os.path.exists(kaggle_dir):
        print(f"Kaggle 数据目录不存在: {kaggle_dir}")
        return 0

    # 查找所有数据集目录
    dataset_dirs = glob.glob(os.path.join(kaggle_dir, "*"))
    if not dataset_dirs:
        print("未找到任何下载的数据集")
        return 0

    # 收集数据集信息
    datasets = []
    for dataset_dir in dataset_dirs:
        metadata_file = os.path.join(dataset_dir, "metadata.json")
        if not os.path.exists(metadata_file):
            continue

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # 应用过滤器（如果有）
            if args.filter:
                filter_key, filter_value = args.filter.split("=", 1)
                if filter_key not in metadata or str(metadata[filter_key]) != filter_value:
                    continue

            # 计算原始数据和 Parquet 数据的大小
            original_size = 0
            parquet_size = 0
            parquet_dir = os.path.join(dataset_dir, "parquet")

            # 如果存在原始数据目录
            original_dir = os.path.join(dataset_dir, "original")
            if os.path.exists(original_dir):
                for root, _, files in os.walk(original_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        original_size += os.path.getsize(file_path)

            # 如果存在 Parquet 数据目录
            if os.path.exists(parquet_dir):
                for root, _, files in os.walk(parquet_dir):
                    for file in files:
                        if file.endswith(".parquet"):
                            file_path = os.path.join(root, file)
                            parquet_size += os.path.getsize(file_path)

            # 格式化大小信息
            original_size_mb = original_size / 1024 / 1024
            parquet_size_mb = parquet_size / 1024 / 1024
            compression_ratio = parquet_size / original_size if original_size > 0 else 0

            # 收集基本信息
            dataset_info = {
                "id": metadata.get("id", "unknown"),
                "name": metadata.get("name", "unknown"),
                "owner": metadata.get("owner", "unknown"),
                "timestamp": metadata.get("timestamp", "unknown"),
                "status": metadata.get("status", "unknown"),
                "files": len(metadata.get("files", [])),
                "original_size": f"{original_size_mb:.2f} MB",
                "parquet_size": f"{parquet_size_mb:.2f} MB",
                "compression_ratio": f"{compression_ratio:.2f}" if compression_ratio > 0 else "N/A",
                "path": dataset_dir
            }

            datasets.append(dataset_info)

        except Exception as e:
            print(f"读取元数据文件 {metadata_file} 失败: {e}")

    if not datasets:
        print("未找到符合条件的数据集")
        return 0

    # 输出结果
    if args.format == "json":
        # JSON 格式输出
        json.dump(datasets, sys.stdout, ensure_ascii=False, indent=2)
    elif args.format == "csv":
        # CSV 格式输出
        writer = csv.DictWriter(sys.stdout, fieldnames=datasets[0].keys())
        writer.writeheader()
        writer.writerows(datasets)
    else:
        # 表格格式输出
        if args.detail:
            # 详细表格
            headers = ["ID", "名称", "所有者", "时间", "状态", "文件数", "原始大小", "Parquet大小", "压缩比"]
            rows = [
                [d["id"], d["name"], d["owner"], d["timestamp"], d["status"], d["files"],
                 d["original_size"], d["parquet_size"], d["compression_ratio"]]
                for d in datasets
            ]
        else:
            # 简单表格
            headers = ["名称", "所有者", "文件数", "原始大小", "状态"]
            rows = [
                [d["name"], d["owner"], d["files"], d["original_size"], d["status"]]
                for d in datasets
            ]

        print(tabulate.tabulate(rows, headers=headers, tablefmt="psql"))

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """
    主函数，程序入口点。

    参数:
        argv: 命令行参数，默认为 None 使用 sys.argv

    返回:
        int: 退出状态码
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # 设置日志级别
    log_level = getattr(logging, args.log_level)
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    if not args.command:
        parser.print_help()
        return 0

    # 处理子命令
    if args.command == "download":
        return handle_download(args)
    elif args.command == "convert":
        return handle_convert(args)
    elif args.command == "config":
        return handle_config(args)
    elif args.command == "list":
        return handle_list(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())