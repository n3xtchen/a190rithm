import tensorflow as tf
from typing import Dict, Any, List, Optional
import json
import tabulate
import statistics

class TFRecordViewer:
    """
    TFRecord 文件查看器，用于读取和解析 tf.train.Example 格式。
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_records(self, limit: Optional[int] = 5) -> List[Dict[str, Any]]:
        """
        获取 TFRecord 文件中的记录。

        参数:
            limit: 限制获取的记录数量，None 表示全部。

        返回:
            List[Dict[str, Any]]: 解析后的记录列表。
        """
        dataset = tf.data.TFRecordDataset(self.file_path)
        if limit:
            dataset = dataset.take(limit)

        records = []
        for raw_record in dataset:
            example = tf.train.Example()
            example.ParseFromString(raw_record.numpy())
            records.append(self._parse_example(example))

        return records

    def _parse_example(self, example: tf.train.Example) -> Dict[str, Any]:
        """
        解析 tf.train.Example 对象为字典格式。
        """
        res = {}
        for key, feature in example.features.feature.items():
            kind = feature.WhichOneof('kind')
            if kind == 'bytes_list':
                res[key] = [v for v in feature.bytes_list.value]
            elif kind == 'float_list':
                res[key] = [v for v in feature.float_list.value]
            elif kind == 'int64_list':
                res[key] = [v for v in feature.int64_list.value]
        return res

    def get_summary(self) -> Dict[str, str]:
        """
        获取数据结构的摘要（字段名和大致类型）。
        """
        dataset = tf.data.TFRecordDataset(self.file_path)
        for raw_record in dataset.take(1):
            example = tf.train.Example()
            example.ParseFromString(raw_record.numpy())

            summary = {}
            for key, feature in example.features.feature.items():
                kind = feature.WhichOneof('kind')
                summary[key] = kind
            return summary
        return {}

    @staticmethod
    def _prepare_record_for_display(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单条记录以备显示。
        """
        formatted = {}
        for k, v in record.items():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], bytes):
                try:
                    formatted[k] = [x.decode('utf-8') for x in v]
                except UnicodeDecodeError:
                    formatted[k] = [str(x) for x in v]
            else:
                formatted[k] = v
        return formatted

    @staticmethod
    def format_record(record: Dict[str, Any]) -> str:
        """
        格式化单条记录为 JSON。
        """
        formatted = TFRecordViewer._prepare_record_for_display(record)
        return json.dumps(formatted, indent=2, ensure_ascii=False)

    def format_records_as_table(self, records: List[Dict[str, Any]]) -> str:
        """
        格式化多条记录为表格。
        """
        if not records:
            return "没有数据可显示"

        # 收集所有表头并准备数据行
        headers = sorted(list(records[0].keys()))
        rows = []
        for record in records:
            prepared = self._prepare_record_for_display(record)
            row = []
            for h in headers:
                val = prepared.get(h, "")
                if isinstance(val, list):
                    if len(val) == 1:
                        row.append(val[0])
                    else:
                        row.append(str(val))
                else:
                    row.append(val)
            rows.append(row)

        return tabulate.tabulate(rows, headers=headers, tablefmt="psql")

    def get_statistics(self, limit: Optional[int] = 1000) -> str:
        """
        分析 TFRecord 文件的统计信息。
        """
        records = self.get_records(limit=limit)
        if not records:
            return "没有记录可以分析。"

        stats_data = {}
        for record in records:
            for key, val in record.items():
                if key not in stats_data:
                    stats_data[key] = []
                # 展平列表以便统计
                if isinstance(val, list):
                    stats_data[key].extend(val)
                else:
                    stats_data[key].append(val)

        headers = ["Feature", "Type", "Count", "Unique", "Mean/Mode", "Min", "Max"]
        rows = []

        for key, vals in sorted(stats_data.items()):
            count = len(vals)
            if not vals:
                rows.append([key, "N/A", 0, 0, "-", "-", "-"])
                continue

            # 检测类型
            first_val = vals[0]
            if isinstance(first_val, (int, float)):
                v_type = "Numeric"
                v_min = min(vals)
                v_max = max(vals)
                v_mean = round(statistics.mean(vals), 4)
                v_unique = len(set(vals))
                rows.append([key, v_type, count, v_unique, v_mean, v_min, v_max])
            elif isinstance(first_val, bytes):
                v_type = "Bytes"
                v_unique = len(set(vals))
                try:
                    # 尝试找出众数
                    v_mode = statistics.mode([v.decode('utf-8') for v in vals])
                except Exception:
                    v_mode = "-"
                rows.append([key, v_type, count, v_unique, v_mode, "-", "-"])
            else:
                rows.append([key, type(first_val).__name__, count, len(set(vals)), "-", "-", "-"])

        return tabulate.tabulate(rows, headers=headers, tablefmt="psql")
