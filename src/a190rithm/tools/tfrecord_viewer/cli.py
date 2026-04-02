import argparse
import sys
import os
from .viewer import TFRecordViewer

def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器。
    """
    parser = argparse.ArgumentParser(
        prog="tfrecord-viewer",
        description="查看和检查 TFRecord 文件中的 tf.train.Example 记录"
    )

    parser.add_argument(
        "path",
        help="TFRecord 文件路径"
    )

    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=5,
        help="显示记录的数量 (默认: 5)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="显示所有记录 (慎用)"
    )

    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="仅显示数据结构的摘要 (字段名和类型)"
    )

    parser.add_argument(
        "--format", "-f",
        choices=["json", "table"],
        default="table",
        help="输出格式 (默认: table)"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="统计视角 (分析特征分布)"
    )

    return parser

def main() -> int:
    """
    主函数，工具入口。
    """
    parser = create_parser()
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"错误: 文件不存在: {args.path}")
        return 1

    try:
        viewer = TFRecordViewer(args.path)

        if args.summary:
            summary = viewer.get_summary()
            if not summary:
                print("错误: 无法获取数据摘要，文件可能为空。")
                return 1
            print("TFRecord 数据摘要:")
            for key, kind in summary.items():
                print(f"  - {key}: {kind}")
            return 0

        if args.stats:
            print(f"统计分析 (分析前 {args.limit if not args.all else '全部'} 条记录):")
            limit = None if args.all else args.limit
            print(viewer.get_statistics(limit=limit))
            return 0

        limit = None if args.all else args.limit
        records = viewer.get_records(limit=limit)

        if not records:
            print("未找到记录或解析失败。")
            return 0

        if args.format == "table":
            print(f"显示 {len(records)} 条记录 (表格格式):")
            print(viewer.format_records_as_table(records))
        else:
            print(f"显示 {len(records)} 条记录 (JSON 格式):")
            for i, record in enumerate(records):
                print(f"--- 记录 {i+1} ---")
                print(viewer.format_record(record))
                print()

        return 0

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
