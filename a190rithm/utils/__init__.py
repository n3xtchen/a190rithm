"""
组件库
"""

import random
from datetime import timedelta

import numpy as np
import torch

def flat_accuracy(preds, labels):
    """
    准确率
    """
    pred_flat = np.argmax(preds, axis=1)
    # labels_flat = np.argmax(labels).flatten()
    return int(np.sum(pred_flat == labels).flatten()) / len(labels)

def format_time(elapsed: float):
    """
    时间格式化
    Takes a time in seconds and 
    returns a string hh:mm:ss
    """
    elapsed_rounded = int(round((elapsed)))

    # Format as hh:mm:ss
    return str(timedelta(seconds=elapsed_rounded))

def init_seed(seed_val: int):
    """
    Set the seed value all over the place to make this reproducible.
    """
    random.seed(seed_val)
    np.random.seed(seed_val)
    torch.manual_seed(seed_val)
    torch.cuda.manual_seed_all(seed_val)
