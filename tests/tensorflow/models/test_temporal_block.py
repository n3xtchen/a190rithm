import tensorflow as tf
import numpy as np
import pytest
from a190rithm.tensorflow.blocks.temporal import TemporalBlock

def test_temporal_block_init():
    # This should fail with the current implementation
    block = TemporalBlock(filter_size=32, kernel_size=3)
    assert block.filter_size == 32

def test_temporal_block_call():
    # This should fail with the current implementation
    block = TemporalBlock(filter_size=32, kernel_size=3)
    # Assuming input shape is (batch, time, channels)
    x = tf.random.normal((1, 10, 16))
    out = block(x)
    assert out.shape == (1, 10, 32)
