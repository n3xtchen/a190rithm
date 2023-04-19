"""
文本分类
"""

import random
import time

import numpy as np
import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers.models.bert.modeling_bert import \
    BertForSequenceClassification
from transformers.models.bert.tokenization_bert import BertTokenizer
from transformers.optimization import get_linear_schedule_with_warmup

from a190rithm.utils import flat_accuracy, format_time

class TextTokenizor:
    """
    分词
    """
    def __init__(self, pretrain_model_path: str, add_special_tokens=False):
        self.model = BertTokenizer.from_pretrained(pretrain_model_path)
        self.add_special_tokens = add_special_tokens

    def tokenize(self, text: str):
        """
        分词
        """
        return self.model.encode(text, add_special_tokens=self.add_special_tokens)

    def tokenize_plus(self, text: str, max_token_size: int):
        """
        填充 & 截断长度
        """
        return self.model.encode_plus(
            text,  # 输入文本
            add_special_tokens=True,  # 添加 '[CLS]' 和 '[SEP]'
            max_length=max_token_size,
            padding="max_length",  # 填充 & 截断长度
            return_attention_mask=True,  # 返回 attn. masks.
            return_tensors='pt',  # 返回 pytorch tensors 格式的数据
        )

class TextClassification:
    """
    文本分类器
    """

    def __init__(self,
                 pretrain_model_path: str,
                 category_size=2,
                 epochs=4,
                 learning_rate=5e-5,
                 adam_epsilon=1e-8):
        self.pretrain_model_path = pretrain_model_path
        self.category_size = category_size

        # 训练 epochs。 BERT 作者建议在 2 和 4 之间，设大了容易过拟合
        self.epochs = epochs

        # We'll store a number of quantities such as training and validation loss,
        # validation accuracy, and timings.
        self.training_stats = []

        self.device = "cpu"
        self.seed_val = 42

        self.model: BertForSequenceClassification = BertForSequenceClassification.from_pretrained(
             self.pretrain_model_path,
             num_labels=self.category_size,
             output_attentions=False,
             output_hidden_states=False)
        self.model.to(self.device)

        self.learning_rate = learning_rate
        self.adam_epsilon = adam_epsilon
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.learning_rate,  # args.learning_rate - default is 5e-5
            eps=self.adam_epsilon   # args.adam_epsilon  - default is 1e-8
        )

    def set_seed(self, seed_val: int):
        """
        设置种子值
        """
        self.seed_val = seed_val

    def init_seed(self):
        """
        Set the seed value all over the place to make this reproducible.
        """
        random.seed(self.seed_val)
        np.random.seed(self.seed_val)
        torch.manual_seed(self.seed_val)
        torch.cuda.manual_seed_all(self.seed_val)

    def to(self, device):
        """
        切换硬件
        """
        self.device = device
        self.model.to(device)

    def train(self, train_dataloader: DataLoader, validation_dataloader: DataLoader):
        """
        模型训练
        """
        # 总的训练样本数
        total_steps = len(train_dataloader) * self.epochs

        # 创建学习率调度器
        scheduler = get_linear_schedule_with_warmup(
            self.optimizer, num_warmup_steps=0, num_training_steps=total_steps)

        self.init_seed()

        for epoch_i in range(0, self.epochs):

            # ========================================
            #               Training
            # ========================================

            # Perform one full pass over the training set.

            print("")
            print(f'======== Epoch {epoch_i+1:} / {self.epochs:} ========')
            print('Training...')

            # Measure how long the training epoch takes.
            epoch_start_time = time.time()

            # Reset the total loss for this epoch.
            epoch_train_loss = 0

            batch_loss = 0
            # Put the model into training mode. Don't be mislead--the call to
            # `train` just changes the *mode*, it doesn't *perform* the training.
            # `dropout` and `batchnorm` layers behave differently during training
            self.model.train()

            # For each batch of training data...
            for step, batch in enumerate(train_dataloader):
                # Progress update every 40 batches.
                if step % 40 == 0 and not step == 0:
                    elapsed = format_time(time.time() - epoch_start_time)

                    print((
                        f'  Batch {step:>5,}  of  {len(train_dataloader):>5,}. '
                        f'     Loss: {batch_loss:.4f}.'
                        f'     Elapsed: {elapsed:}.'))

                b_input_ids = batch["input_ids"].to(self.device)
                b_input_mask = batch["attention_mask"].to(self.device)
                b_labels = batch["label"].to(self.device)

                # Always clear any previously calculated gradients before performing a
                # backward pass.
                self.model.zero_grad()

                # Perform a forward pass (evaluate the model on this training batch).
                model = self.model(b_input_ids,
                          token_type_ids=None,
                          attention_mask=b_input_mask,
                          labels=b_labels)

                # Accumulate the training loss over all of the batches so that we can
                # calculate the average loss at the end. `loss` is a Tensor containing a
                # single value;
                batch_loss = model.loss.item()
                epoch_train_loss += batch_loss

                # Perform a backward pass to calculate the gradients.
                model.loss.backward()

                # Clip the norm of the gradients to 1.0.
                # This is to help prevent the "exploding gradients" problem.
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

                # Update parameters and take a step using the computed gradient.
                # The optimizer dictates the "update rule"--how the parameters are
                # modified based on their gradients, the learning rate, etc.
                self.optimizer.step()

                # Update the learning rate.
                scheduler.step()

            # Calculate the average loss over all of the batches.
            avg_epoch_train_loss = epoch_train_loss / len(train_dataloader)

            # Measure how long this epoch took.
            epoch_elapsed = time.time() - epoch_start_time
            epoch_training_time = format_time(epoch_elapsed)

            print("")
            print(f"  Average training loss: {avg_epoch_train_loss:.2f}")
            print(f"  Training epcoh took: {epoch_training_time:}")

            # # ========================================
            # #               Validation
            # # ========================================
            # # After the completion of each training epoch, measure our performance on
            # # our validation set.

            print("")
            print("Running Validation...")

            avg_val_loss, avg_val_accuracy, val_elapsed = self.test(validation_dataloader).values()
            validation_time = format_time(val_elapsed)

            print(f"  Validation Loss: {avg_val_loss:.2f}")
            print(f"  Validation Accuracy: {avg_val_accuracy:.2f}")
            print(f"  Validation took: {validation_time:}")

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

        # Put the model in evaluation mode--the dropout layers behave differently
        # during evaluation.
        self.model.eval()

        # Tracking variables
        total_eval_accuracy = 0
        total_eval_loss = 0
        # nb_eval_steps = 0

        # Evaluate data for one epoch
        for batch in dataloader:
            b_input_ids = batch["input_ids"].to(self.device)
            b_input_mask = batch["attention_mask"].to(self.device)
            b_labels = batch["label"].to(self.device)

            # Tell pytorch not to bother with constructing the compute graph during
            # the forward pass, since this is only needed for backprop (training).
            with torch.no_grad():
                # Forward pass, calculate logit predictions.
                model = self.model(b_input_ids,
                           token_type_ids=None,
                           attention_mask=b_input_mask,
                           labels=b_labels)

            # Accumulate the validation loss.
            total_eval_loss += model.loss.item()

            # Move logits and labels to CPU
            logits = model.logits.detach().cpu().numpy()
            label_ids = b_labels.to('cpu').numpy()

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
