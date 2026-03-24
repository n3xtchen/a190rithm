import tensorflow as tf
tf.random.set_seed(42)
import tensorflow as tf
import numpy as np
import random
import os
from a190rithm.tensorflow.blocks.temporal import TemporalAttentionBlock

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def test_weight_consistency_with_seeds():
    d_model = 16
    seq_len = 5
    x = tf.random.normal((1, seq_len, d_model))

    print("\n--- 场景 A: 只设置一次种子，先后创建两个 Block ---")
    set_seed(42)
    block1 = TemporalAttentionBlock(d_model=d_model)
    _ = block1(x) # 触发权重初始化

    block2 = TemporalAttentionBlock(d_model=d_model)
    _ = block2(x) # 触发权重初始化

    # 验证权重是否不同 (因为随机数流在 block1 后已经改变)
    w1 = block1.q_layer.get_weights()[0]
    w2 = block2.q_layer.get_weights()[0]

    diff = np.abs(w1 - w2).sum()
    print(f"场景 A 权重差异总和: {diff:.6f}")
    assert diff > 0, "错误：只设置一次种子时，两个 Block 的权重竟然完全一样！"
    print("[OK] 证实：只设置一次种子不足以保证多个实例权重相同。")

    print("\n--- 场景 B: 每次创建 Block 前都重置相同的种子 ---")
    set_seed(42)
    block3 = TemporalAttentionBlock(d_model=d_model)
    _ = block3(x)

    set_seed(42) # 再次重置
    block4 = TemporalAttentionBlock(d_model=d_model)
    _ = block4(x)

    # 验证权重是否完全一致
    w3 = block3.q_layer.get_weights()[0]
    w4 = block4.q_layer.get_weights()[0]

    diff_b = np.abs(w3 - w4).sum()
    print(f"场景 B 权重差异总和: {diff_b:.6f}")
    np.testing.assert_array_almost_equal(w3, w4, decimal=6, err_msg="场景 B 失败：重置种子后权重仍不一致")
    print("[OK] 证实：每次初始化前重置种子可以保证权重一致。")

if __name__ == "__main__":
    test_weight_consistency_with_seeds()
