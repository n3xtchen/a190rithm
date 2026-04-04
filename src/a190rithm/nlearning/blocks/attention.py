
from a190rithm.nlearning.layers import linear, softmax


def multi_head_attention(x, n_head, head_dim,  w_q, w_k, w_v, keys, values):
    """
    x: 输入向量
    head_dim: 多头注意力头的数量
    w_{q, k, v}: qkv 的权重矩阵
    keys, values: k, v 的缓存
    """
    q = linear(x, w_q)
    k = linear(x, w_k)
    v = linear(x, w_v)
    keys.append(k)
    values.append(v)

    x_attn = []
    for h in range(n_head):
        hs = h * head_dim
        q_h = q[hs:hs+head_dim]
        k_h = [ki[hs:hs+head_dim] for ki in keys]
        v_h = [vi[hs:hs+head_dim] for vi in values]
        attn_logits = [sum(q_h[j] * k_h[t][j] for j in range(head_dim)) / head_dim**0.5 for t in range(len(k_h))]
        attn_weights = softmax(attn_logits)
        head_out = [sum(attn_weights[t] * v_h[t][j] for t in range(len(v_h))) for j in range(head_dim)]
        x_attn.extend(head_out)

    return x_attn

