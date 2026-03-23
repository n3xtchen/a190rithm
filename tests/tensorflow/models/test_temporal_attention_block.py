import tensorflow as tf
import pytest
import numpy as np
from a190rithm.tensorflow.models.SpatioTemporalNet import TemporalAttentionBlock

def test_temporal_attention_block_init():
    # This should fail if there's any immediate error in __init__
    block = TemporalAttentionBlock(d_model=32)
    assert True

def test_temporal_attention_block_leakage():
    # 验证是否存在数据泄漏：改变未来的输入不应影响过去的输出
    block = TemporalAttentionBlock(d_model=32)

    # 构造两个输入，只有最后一个时间步不同
    x1 = tf.random.normal((1, 10, 32))
    x2 = tf.identity(x1).numpy()
    x2[0, -1, :] += 10.0  # 修改最后一个时间步
    x2 = tf.convert_to_tensor(x2)

    out1 = block(x1)
    out2 = block(x2)

    # 检查前 9 个时间步的输出是否一致
    # 如果不一致，说明存在数据泄漏
    np.testing.assert_array_almost_equal(
        out1.numpy()[:, :9, :],
        out2.numpy()[:, :9, :],
        decimal=5,
        err_msg="Detected Data Leakage: Future values affected past outputs!"
    )
