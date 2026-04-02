import os
import tensorflow as tf
import pytest
from a190rithm.tools.tfrecord_viewer.viewer import TFRecordViewer

def create_dummy_tfrecord(path):
    """
    创建一个包含 dummy 数据的 TFRecord 文件。
    """
    with tf.io.TFRecordWriter(path) as writer:
        for i in range(3):
            feature = {
                'id': tf.train.Feature(int64_list=tf.train.Int64List(value=[i])),
                'name': tf.train.Feature(bytes_list=tf.train.BytesList(value=[f'record_{i}'.encode('utf-8')])),
                'score': tf.train.Feature(float_list=tf.train.FloatList(value=[i * 1.5])),
            }
            example = tf.train.Example(features=tf.train.Features(feature=feature))
            writer.write(example.SerializeToString())

@pytest.fixture
def dummy_tfrecord(tmp_path):
    path = os.path.join(tmp_path, "test.tfrecord")
    create_dummy_tfrecord(path)
    return path

def test_viewer_get_records(dummy_tfrecord):
    viewer = TFRecordViewer(dummy_tfrecord)
    records = viewer.get_records(limit=2)

    assert len(records) == 2
    assert records[0]['id'] == [0]
    assert records[0]['name'] == [b'record_0']
    assert records[0]['score'] == [0.0]

    assert records[1]['id'] == [1]
    assert records[1]['name'] == [b'record_1']
    assert records[1]['score'] == [1.5]

def test_viewer_get_summary(dummy_tfrecord):
    viewer = TFRecordViewer(dummy_tfrecord)
    summary = viewer.get_summary()

    assert summary['id'] == 'int64_list'
    assert summary['name'] == 'bytes_list'
    assert summary['score'] == 'float_list'

def test_viewer_format_record(dummy_tfrecord):
    viewer = TFRecordViewer(dummy_tfrecord)
    records = viewer.get_records(limit=1)
    formatted = viewer.format_record(records[0])

    assert '"id": [' in formatted
    assert '0' in formatted
    assert '"name": [' in formatted
    assert '"record_0"' in formatted
    assert '"score": [' in formatted
    assert '0.0' in formatted
