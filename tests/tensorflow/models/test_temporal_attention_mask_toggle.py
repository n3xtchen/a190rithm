import os
# 必须在导入 tensorflow 之前设置环境变量以确保确定性
os.environ['TF_DETERMINISTIC_OPS'] = '1'
os.environ['TF_CUDNN_DETERMINISTIC'] = '1'
os.environ['PYTHONHASHSEED'] = '42'

import tensorflow as tf
import pytest
import numpy as np
import random
from a190rithm.tensorflow.blocks.temporal import TemporalAttentionBlock

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)

def test_causal_mask_effectiveness_with_seeds_only():
    """
    通过在每次初始化前重置种子，验证在不手动复制权重的情况下，
    Mask 是否能有效且公平地阻止数据泄漏。
    """
    seq_len = 10
    d_model = 32

    # 提前构造输入数据
    set_seed(42)
    x1 = tf.random.normal((1, seq_len, d_model))
    x2 = x1.numpy().copy()
    x2[0, -1, :] += 10.0  # 仅修改最后一个时间步
    x2 = tf.convert_to_tensor(x2)

    # --- 情况 1: 开启 Mask (causal=True) ---
    set_seed(42) # 重置种子确保初始化确定性
    block_with_mask = TemporalAttentionBlock(d_model=d_model, causal=True)
    _ = block_with_mask(x1) # 触发权重初始化

    out1_with = block_with_mask(x1)
    out2_with = block_with_mask(x2)

    # 验证：前 seq_len-1 个时间步应该【完全一致】
    np.testing.assert_array_almost_equal(
        out1_with.numpy()[:, :-1, :],
        out2_with.numpy()[:, :-1, :],
        decimal=5,
        err_msg="Causal=True 失败：开启 Mask 后仍然检测到数据泄漏"
    )

    # --- 情况 2: 关闭 Mask (causal=False) ---
    set_seed(42) # 【关键】再次重置完全相同的种子，替代手动复制权重
    block_no_mask = TemporalAttentionBlock(d_model=d_model, causal=False)
    _ = block_no_mask(x1) # 权重现在应该和 block_with_mask 完全一致

    out1_no = block_no_mask(x1)
    out2_no = block_no_mask(x2)

    # 验证：前 seq_len-1 个时间步应该【不一致】
    # 这证明了两个 Block 的初始权重确实是一样的，唯一的变量是 Mask 开关
    with pytest.raises(AssertionError):
        np.testing.assert_array_almost_equal(
            out1_no.numpy()[:, :-1, :],
            out2_no.numpy()[:, :-1, :],
            decimal=5
        )

    # 额外验证：两个 Block 的权重是否真的完全一样（双重保险）
    w_with = block_with_mask.q_layer.get_weights()[0]
    w_no = block_no_mask.q_layer.get_weights()[0]
    np.testing.assert_array_almost_equal(w_with, w_no, decimal=6, err_msg="种子重置失败：两个 Block 权重不一致")

    print("\n[OK] 仅通过重置种子成功保证了权重一致，并验证了 Mask 的有效性。")

if __name__ == "__main__":
    test_causal_mask_effectiveness_with_seeds_only()
