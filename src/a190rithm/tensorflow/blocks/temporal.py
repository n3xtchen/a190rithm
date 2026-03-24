

import tensorflow as tf

class TemporalBlock(tf.keras.layers.Layer):

    def __init__(self, filter_size, kernel_size,
                 dilation=1, stride=1, activation="relu", dropout_rate=0.2):
        super(TemporalBlock, self).__init__()

        # filter 数量和 input 的 channel 数量不一致，输入输出的形状就会不一致
        self.conv1 = tf.keras.layers.Conv1D(filters=filter_size,
                                           kernel_size=kernel_size,
                                           dilation_rate=dilation,
                                           strides=stride, padding="causal")

        self.act_layer = tf.keras.layers.Activation(activation)
        self.dropout = tf.keras.layers.Dropout(dropout_rate)

        # 卷积和残差的对齐
        self.downsample = None
        self.filter_size = filter_size

    def build(self, input_shape):
        """
        当模型第一次接受数据的时候，会自动调用 build，并把数据 input 传进来
        """
        if input_shape[-1] != self.filter_size:
            # kernel_size=1 不会出现时间穿越
            self.downsample = tf.keras.layers.Conv1D(filters=self.filter_size,
                                                    kernel_size=1, padding="same")

    def call(self, x):

        out = self.conv1(x)
        out = self.act_layer(out)
        out = self.dropout(out)

        res = x if self.downsample is None else self.downsample(x)

        return tf.nn.relu(out + res)

class TemporalAttentionBlock(tf.keras.layers.Layer):

    def __init__(self, d_model=512, causal=True):

        super(TemporalAttentionBlock, self).__init__()

        self.q_layer = tf.keras.layers.Dense(d_model)
        self.k_layer = tf.keras.layers.Dense(d_model)
        self.v_layer = tf.keras.layers.Dense(d_model)

        self.ln_layer = tf.keras.layers.LayerNormalization()
        self.output_layer = tf.keras.layers.Dense(1)
        self.causal = causal

    def call(self, x):

        q = self.q_layer(x)
        k = self.k_layer(x)
        v = self.v_layer(x)

        qk = tf.matmul(q, k, transpose_b=True)
        dk = tf.cast(tf.shape(k)[-1], tf.float32)
        scaled_attention_logits = qk/tf.math.sqrt(dk)

        if self.causal:
            # 添加 Look-ahead Mask
            seq_len = tf.shape(x)[1]
            mask = 1 - tf.linalg.band_part(tf.ones((seq_len, seq_len)), -1, 0)
            # 将 mask 转换为极小值，使得 softmax 后权重接近 0
            scaled_attention_logits += (mask * -1e9)

        scores = tf.nn.softmax(scaled_attention_logits)

        output = tf.matmul(scores, v)
        x = tf.nn.relu(x + output)

        x = self.ln_layer(x)

        output = self.output_layer(x)

        return output














