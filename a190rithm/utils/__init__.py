"""
组件库
"""

from datetime import timedelta
import numpy as np

def flat_accuracy(preds, labels):
    """
    准确率
    """
    pred_flat = np.argmax(preds, axis=1)
    # labels_flat = np.argmax(labels).flatten()
    return int(np.sum(pred_flat == labels).flatten()) / len(labels)

def format_time(elapsed: int):
    """
    时间格式化
    Takes a time in seconds and returns a string hh:mm:ss
    """
    elapsed_rounded = int(round((elapsed)))

    # Format as hh:mm:ss
    return str(timedelta(seconds=elapsed_rounded))
