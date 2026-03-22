

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

