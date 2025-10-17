"""
测试组件库
"""

import numpy as np
from a190rithm.utils import flat_accuracy

def test_accuracy():
    """
    准确率计算
    """
    real = np.array([1, 1])
    pred = np.array([[0.2, 0.1], [0.1, 0.2]])

    assert flat_accuracy(pred, real)==0.5
