"""
gpt 分类器
"""
import time

import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import GPT2Tokenizer, GPT2ForSequenceClassification
from transformers.optimization import get_linear_schedule_with_warmup

from a190rithm.utils import flat_accuracy, format_time, init_seed


class GPT2TokenizerWithMaxLength(GPT2Tokenizer):
    """
    为 BertTokenize 添加最大长度
    todo: 添加自定义配置
    - set_config(key, val), get_config(key)
    """

    def set_max_length(self, max_length: int, pad_token=None):
        """
        设置最长token数
        """
        self.pad_token = pad_token or self.eos_token
        self.init_kwargs["max_length"] = max_length
        self.init_kwargs["add_special_tokens"] = True

    @property
    def max_length(self):
        """
        读取最长token数
        """
        return self.init_kwargs["max_length"]

    def evaluate(self, text: list[str]):
        """
        根据配置填充和截断长度
        """
        return self(
            text,  # 输入文本
            max_length=self.max_length,
            padding="max_length",
            return_tensors='pt',  # 返回 pytorch tensors 格式的数据
        )


class GPT2TextClassification:
    """
    分类器
    """
    # 默认超参数
    hyper_params = {
        "seed_val": 42,
        "pad_token_id": 50256,
        "epochs": 4,  # 训练 epochs。 BERT 作者建议在 2 和 4 之间，设大了容易过拟合
        "learning_rate": 5e-5,
        "epsilon": 1e-8
    }

    _model: GPT2ForSequenceClassification = None
    _optimizer: AdamW = None

    # 训练效果统计
    training_stats = []

    def __init__(self, pretrain_model_path: str, category_size=2, **kwargs):
        self.pretrain_model_path = pretrain_model_path
        self.category_size = category_size

        for hyper_param in self.hyper_params:
            if hyper_param in kwargs:
                self.hyper_params[hyper_param] = kwargs[hyper_param]

    def set_seed(self, seed_val: int):
        """
        设置种子值
        """
        self.hyper_params["seed_val"] = seed_val

    @property
    def device(self):
        """
        模型配置的设备
        """
        return self.model.device

    # pylint: disable=invalid-name
    def to(self, device: str):
        """
        切换设备
        """
        self.model.to(device)

    @property
    def model(self):
        """
        初始化和获取模型
        """
        if self._model is None:
            self._model = GPT2ForSequenceClassification.from_pretrained(
                self.pretrain_model_path, num_labels=self.category_size)
            self._model.config.pad_token_id = self.hyper_params["pad_token_id"]
        return self._model

    @property
    def optimizer(self):
        """获取或者初始化优化器"""
        if self._optimizer is None:
            self._optimizer = AdamW(
                self.model.parameters(),
                lr=self.hyper_params[
                    "learning_rate"],  # args.learning_rate - default is 5e-5
                eps=self.hyper_params[
                    "epsilon"]  # args.adam_epsilon  - default is 1e-8
            )
        return self._optimizer

    def train(self, train_dataloader, validation_dataloader):
        """
        模型训练
        """
        init_seed(self.hyper_params["seed_val"])

        # 创建学习率调度器
        scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=0,
            num_training_steps=len(train_dataloader) *
            self.hyper_params["epochs"])

        for epoch_i in range(0, self.hyper_params["epochs"]):

            # ========================================
            #               Training
            # ========================================

            # Perform one full pass over the training set.

            print("")
            print(
                f'======== Epoch {epoch_i+1:} / {self.hyper_params["epochs"]:} ========'
            )
            print('Training...')

            # Measure how long the training epoch takes.
            epoch_start_time = time.time()

            # Reset the total loss for this epoch.
            epoch_train_loss = 0

            # 进入训练模式
            self.model.train()

            # For each batch of training data...
            for step, batch in enumerate(train_dataloader):

                self.model.zero_grad()

                # Perform a forward pass (evaluate the model on this training batch).
                loss, _ = self.model.forward(
                    batch["input_ids"].to(self.device),
                    attention_mask=batch["attention_mask"].to(self.device),
                    labels=batch["label"].to(self.device)).to_tuple()[:2]

                # Accumulate the training loss over all of the batches so that we can
                # calculate the average loss at the end. `loss` is a Tensor containing a
                # single value;
                epoch_train_loss += loss.item()

                # Progress update every 40 batches.
                if step % 40 == 0 and not step == 0:
                    print((
                        f'  Batch {step:>5,}  of  {len(train_dataloader):>5,}. '
                        f'     Loss: {loss.item():.4f}.'
                        f'     Elapsed: {format_time(time.time() - epoch_start_time):}.'
                    ))

                loss.backward()

                # Clip the norm of the gradients to 1.0.
                # This is to help prevent the "exploding gradients" problem.
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

                self.optimizer.step()

                scheduler.step()

            # Calculate the average loss over all of the batches.
            avg_epoch_train_loss = epoch_train_loss / len(train_dataloader)

            # Measure how long this epoch took.
            epoch_elapsed = time.time() - epoch_start_time

            print("")
            print(f"  Average training loss: {avg_epoch_train_loss:.2f}")
            print(f"  Training epcoh took: {format_time(epoch_elapsed):}")

            # # ========================================
            # #               Validation
            # # ========================================
            # # After the completion of each training epoch, measure our performance on
            # # our validation set.

            print("")
            print("Running Validation...")

            avg_val_loss, avg_val_accuracy, val_elapsed = self.test(
                validation_dataloader).values()

            print(f"  Validation Loss: {avg_val_loss:.2f}")
            print(f"  Validation Accuracy: {avg_val_accuracy:.2f}")
            print(f"  Validation took: {format_time(val_elapsed):}")

            # Record all statistics from this epoch.
            self.training_stats.append({
                'epoch': epoch_i + 1,
                'Training Loss': avg_epoch_train_loss,
                'Training Time': epoch_elapsed,
                'Valid. Loss': avg_val_loss,
                'Valid. Accur.': avg_val_accuracy,
                'Validation Time': val_elapsed
            })

    def test(self, dataloader: DataLoader):
        """
        measure our performance on our dataset.
        """
        start_time = time.time()

        # 进入推理模式
        self.model.eval()

        # Tracking variables
        total_eval_accuracy = 0
        total_eval_loss = 0

        for batch in dataloader:
            b_input_ids = batch["input_ids"].to(self.device)
            b_input_mask = batch["attention_mask"].to(self.device)
            b_labels = batch["label"].to(self.device)

            with torch.no_grad():
                loss, logits = self.model.forward(
                    b_input_ids, attention_mask=b_input_mask,
                    labels=b_labels).to_tuple()[:2]

            total_eval_loss += loss.item()

            # detach 相当于深拷贝, 后续的对该值操作和 model.logits 脱钩
            logits = logits.detach().cpu().numpy()
            label_ids = b_labels.cpu().numpy()

            # Calculate the accuracy for this batch of test sentences, and
            # accumulate it over all batches.
            total_eval_accuracy += flat_accuracy(logits, label_ids)

        # Report the final accuracy for this validation run.
        avg_accuracy = total_eval_accuracy / len(dataloader)

        # Calculate the average loss over all of the batches.
        avg_loss = total_eval_loss / len(dataloader)

        # Measure how long the validation run took.
        elapsed = time.time() - start_time

        return {
            "avg_loss": avg_loss,
            "avg_accuracy": avg_accuracy,
            "elapsed": elapsed
        }
