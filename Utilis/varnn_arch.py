# -*- coding: utf-8 -*-
"""VARNN_arch.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1-DPJ-36nL-ZASeyVStPGlc5dTv94YvrG

This neural network architecture, is based on reduced var, and it induced non linearity by using sigmoid activation function.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data as data_utils
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error

class VARNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, dropout_rate=0.7):
        super(VARNN, self).__init__()
        self.hidden_layer = nn.Linear(input_size, hidden_size)
        self.dropout = nn.Dropout(dropout_rate)  # Dropout layer
        self.output_layer = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()

        # Apply Xavier initialization
        nn.init.xavier_uniform_(self.hidden_layer.weight)
        nn.init.xavier_uniform_(self.output_layer.weight)

    def forward(self, x):
        hidden_output = self.relu(self.hidden_layer(x))
        hidden_output = self.dropout(hidden_output)  # Apply dropout
        output = self.output_layer(hidden_output)
        return output
