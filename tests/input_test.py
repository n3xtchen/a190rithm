# vim:fenc=utf-8
#
# Copyright © 2025 n3xtchen <echenwen@gmail.com>
#
# Distributed under terms of the GPL-2.0 license.

"""

"""

import numpy as np
# from keras.layers import LSTM, Dense
from keras.models import Model
from keras.layers import Input, Lambda

def test_input():

    inp = Input(shape=(3,), name="my_input")
    out = Lambda(lambda x: x)(inp)
    model = Model(inputs=inp, outputs=out)

    x = np.array([[1, 2, 3], [4, 5, 6]])

    print(model.predict(x))
