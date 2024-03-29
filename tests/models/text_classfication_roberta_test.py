"""
文本分类测试（GPT）
"""

from datasets.builder import Dataset
from datasets.load import load_dataset
from torch.utils.data import DataLoader

from a190rithm.models.text_classification_roberta import (
    RobertaTextClassification, RobertaTokenizerWithMaxLength)
from a190rithm.utils import format_time

CACHE_DIR = "/Users/nextchen/.cache/huggingface/hub/models--"
MODEL_FILE = (f'{CACHE_DIR}xlm-roberta-base/snapshots/'
              '77de1f7a7e5e737aead1cd880979d4f1b3af6668/')
FINE_TUNE_FILE = '/Users/nextchen/Dev/project_pig/a190rithm/data/fine_tuned_model_reberta'


def test_roberta_tokenizer():
    """
    测试文本分词
    """
    data: Dataset = load_dataset("glue", "cola")
    train_data = data["train"]

    tokenizer = RobertaTokenizerWithMaxLength.from_pretrained(MODEL_FILE)

    train_data = train_data.map(lambda row: {
        "token_size":
        [len(i) for i in tokenizer(row['sentence'])["input_ids"]]
    }, batched=True)
    max_length = max(train_data["token_size"])

    tokenizer.set_max_length(max_length)
    assert tokenizer.max_length == 49

    tokenizer.save_pretrained(FINE_TUNE_FILE)
    max_token_size = RobertaTokenizerWithMaxLength.from_pretrained(
        FINE_TUNE_FILE).init_kwargs["max_length"]
    assert max_token_size == 49

    train_data_proced: Dataset = data["train"].map(
        lambda row: tokenizer.evaluate(row["sentence"]), batched=True)
    for row in train_data_proced:
        assert len(row["input_ids"]) == 49
        assert len(row["attention_mask"]) == 49


def test_robreta_text_classfication():
    """
    测试文本分类
    """
    tokenizer = RobertaTokenizerWithMaxLength.from_pretrained(FINE_TUNE_FILE)
    data: Dataset = load_dataset("glue", "cola")
    train_data: Dataset = data["train"].map(
        lambda row: tokenizer.evaluate(row["sentence"]), batched=True)
    train_data.set_format(type="torch",
                          columns=["input_ids", "attention_mask", "label"])
    train_dataloader = DataLoader(train_data, batch_size=32)
    category_size = len(train_data["label"].unique())
    assert category_size == 2

    validate_data: Dataset = data["validation"].map(
        lambda row: tokenizer.evaluate(row["sentence"]), batched=True)
    validate_data.set_format(type="torch",
                             columns=["input_ids", "attention_mask", "label"])
    validate_dataloader = DataLoader(validate_data, batch_size=32)

    classification = RobertaTextClassification(MODEL_FILE,
                                               epochs=1,
                                               learning_rate=2e-5,
                                               adam_epsilon=1e-8)
    classification.to('mps')
    classification.train(train_dataloader, validate_dataloader)
    classification.model.save_pretrained(FINE_TUNE_FILE)


def test_roberta_text_classfication_inference():
    """
    测试分类模型推理
    """
    print("")
    print('===================== Test ==========================')
    print('Testing...')

    tokenizer = RobertaTokenizerWithMaxLength.from_pretrained(FINE_TUNE_FILE)
    data: Dataset = load_dataset("glue", "cola")
    test_data: Dataset = data["validation"].map(
        lambda row: tokenizer.evaluate(row["sentence"]), batched=True)
    test_data.set_format(type="torch",
                         columns=["input_ids", "attention_mask", "label"])
    test_dataloader = DataLoader(test_data, batch_size=32)

    classification = RobertaTextClassification(FINE_TUNE_FILE)
    classification.to('mps')

    avg_test_loss, avg_test_accuracy, test_elapsed = classification.test(
        test_dataloader).values()
    test_time = format_time(test_elapsed)

    print(f"  Test Loss: {avg_test_loss:.2f}")
    print(f"  Test Accuracy: {avg_test_accuracy:.2f}")
    print(f"  Test took: {test_time:}")
