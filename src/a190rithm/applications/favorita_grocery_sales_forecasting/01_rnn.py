#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 n3xtchen <echenwen@gmail.com>
#
# Distributed under terms of the GPL-2.0 license.

"""
Recurrent Neural Network (RNN) module for sequence modeling.
"""

from keras.layers import LSTM, Dense
from keras.models import Model
from keras.layers import Input
from keras.callbacks import EarlyStopping

class RNNModel:

    def __init__(self, input_shape, output_units, lstm_units=128):
        """
        Initialize the RNN model.

        :param input_shape: Shape of the input data (timesteps, features).
        :param output_units: Number of output units.
        :param lstm_units: Number of LSTM units.
        """
        self.input_shape = input_shape
        self.output_units = output_units
        self.lstm_units = lstm_units
        self.model = self.build_model()

    def build_model(self):
        """
        Build the RNN model architecture.

        :return: Compiled Keras model.
        """
        inputs = Input(shape=self.input_shape)
        x = LSTM(self.lstm_units)(inputs)
        outputs = Dense(self.output_units, activation='softmax')(x)

        model = Model(inputs, outputs)
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        return model

    def train(self, x_train, y_train, x_val, y_val, epochs=50, batch_size=32):
        """
        Train the RNN model.

        :param x_train: Training input data.
        :param y_train: Training target data.
        :param x_val: Validation input data.
        :param y_val: Validation target data.
        :param epochs: Number of training epochs.
        :param batch_size: Size of training batches.
        """
        early_stopping = EarlyStopping(monitor='val_loss', patience=5)
        self.model.fit(x_train, y_train, validation_data=(x_val, y_val),
                       epochs=epochs, batch_size=batch_size,
                       callbacks=[early_stopping])
