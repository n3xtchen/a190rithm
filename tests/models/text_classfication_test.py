"""
文本分类测试
"""

from datasets.builder import Dataset
from datasets.load import load_dataset
from torch.utils.data import DataLoader

from a190rithm.models.text_classification import (TextClassification,
                                                  TextTokenizor)
from a190rithm.utils import format_time

CACHE_DIR="/Users/nextchen/.cache/huggingface/hub/models--"
# MODEL_FILE = (f'{CACHE_DIR}bert-base-multilingual-cased/snapshots/'
#               'fdfce55e83dbed325647a63e7e1f5de19f0382ba/')
MODEL_FILE = (f'{CACHE_DIR}distilbert-base-uncased-distilled-squad/snapshots/'
              'bb133e834d7dab8aa8eb3f04e0435db7a3a1ddc8')

def test_text_classfication():
    """
    测试文本分类
    """
    tokenizer = TextTokenizor(MODEL_FILE, True)
    data : Dataset = load_dataset("glue", "cola")

    data["train"] = data["train"].map(
        lambda row: {"token_size": [len(i) for i in tokenizer.tokenize(row['sentence'])]},
        batched=True)
    max_token_size = max(data["train"]["token_size"])
    assert max_token_size==47

    def proc(text):
        """
        """
        token_plus = tokenizer.tokenize_plus(text, max_token_size)
        return {
            "input_ids": token_plus["input_ids"],
            "attention_mask": token_plus["attention_mask"]
        }
    train_data: Dataset = data["train"].map(lambda row: proc(row["sentence"]), batched=True)
    train_data.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    train_dataloader = DataLoader(train_data, batch_size=32)
    category_size = len(train_data["label"].unique())
    assert category_size == 2

    validate_data: Dataset = data["validation"].map(lambda row: proc(row["sentence"]), batched=True)
    validate_data.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    validate_dataloader = DataLoader(validate_data, batch_size=32)

    classification = TextClassification(MODEL_FILE,
                                        epochs=2,
                                        learning_rate=2e-5,
                                        adam_epsilon=1e-8)
    classification.to('mps')

    classification.train(train_dataloader, validate_dataloader)

    print("")
    print('===================== Test ==========================')
    print('Testing...')

    test_data: Dataset = data["test"].map(lambda row: proc(row["sentence"]), batched=True)
    test_data.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])
    test_dataloader = DataLoader(test_data, batch_size=32)
    avg_test_loss, avg_test_accuracy, test_elapsed = classification.test(test_dataloader).values()
    test_time = format_time(test_elapsed)

    print(f"  Test Loss: {avg_test_loss:.2f}")
    print(f"  Test Accuracy: {avg_test_accuracy:.2f}")
    print(f"  Test took: {test_time:}")
