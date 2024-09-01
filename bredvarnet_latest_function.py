# -*- coding: utf-8 -*-
"""BRedVARNet_latest_function.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1A9feQ7rkyCiaBby-7uQlu22gowKE_UFO

**Description**

This file has neural network version of Vector AutoRegressive Model. that induces non linearity.Code first does data preprocessing from 'mytsdataset' dataloader, after which model is trained model and forecasting is done considering the exogenous variables. this code. Name of the architecture used is 'VARNN'

**Dependancies**

properscoring

mytsdataset_latest

varnn_arch

evaluation

**Arguments**

df : pandas dataframe

exo_test : Test data of exogenous variables - should have m_step observations

lags : Lags

train_size : Size of tarining set

val_size : Size of validation set
               
m_steps : Horizon length
               
hidden_size : Number of hidden units
               
learning_rate : Learning rate

num_epochs : Number of epochs

batch_size : Batch Size

optimizer_type : Type of optimizer

standardise : (True/False) Standardises data

differencing : (True/False) DIfferences data
               
exo : List of names of exogenous variables (None by default)
"""

!pip install properscoring

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data as data_utils
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.api import VAR
from sklearn.metrics import mean_squared_error

import mytsdataset_latest
from mytsdataset_latest import MyTimeSeriesDataset
import varnn_arch
from varnn_arch import VARNN
import evaluation
from evaluation import *

def BRedVARNet(df,
               exo_test,
               lags=2,
               train_size=0.8,
               val_size=0.2,
               m_steps=4,
               hidden_size=6,
               learning_rate=0.01,
               num_epochs=100,
               batch_size=1,
               optimizer_type='SGD',
               standardise=True,
               differencing=True,
               exo=None):
    # Set to gpu mode
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    #########################
    ##### Data Preparation
    ##########################
    input_size = lags * df.shape[1]
    output_size = df.shape[1]

    if exo is not None:
        output_size = df.shape[1] - len(exo)
        endo_cols = df.columns.difference(exo)
        temp = exo.copy()
        temp.extend(endo_cols)
        df = df[temp]
        ##print('df' , df)
    else:
        endo_cols = df.columns

    # Keep exogenous variables first

    # Create MyTimeSeriesDataset object
    dataset = MyTimeSeriesDataset(df=df, lags=lags, horizon_length=m_steps, exo=exo, standardise=standardise, differencing=differencing)

    # Get DataLoaders
    train_loader, val_loader, data_test = dataset.get_myloaders(batch_size)
    #############################
    ##### Training and Validation
    #############################
    # Create the model
    model = VARNN(input_size, hidden_size, output_size,0.5).to(device)

    # Loss and optimizer
    criterion = nn.MSELoss()
    if optimizer_type == 'Adam':
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    elif optimizer_type == 'SGD':
        optimizer = optim.SGD(model.parameters(), lr=learning_rate)
    else:
        raise ValueError("Unsupported optimizer. Please choose 'Adam' or 'SGD'.")


    #scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=10)


    # Training loop with validation
    train_losses = []
    val_losses = []

    for epoch in range(num_epochs):
        # Training
        model.train()
        epoch_train_loss = 0.0

        for X_batch, y_batch in train_loader:
            # Put batch samples to gpu
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)
            #print(y_batch)

            ##print('X_batch' , X_batch)
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_train_loss += loss.item()

        epoch_train_loss /= len(train_loader)
        train_losses.append(epoch_train_loss)

        # Validation
        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                # Put on gpu
                X_batch = X_batch.to(device)
                y_batch = y_batch.to(device)
                val_outputs = model(X_batch)
                val_loss = criterion(val_outputs, y_batch)
                epoch_val_loss += val_loss.item()

        epoch_val_loss /= len(val_loader)
        val_losses.append(epoch_val_loss)
        #scheduler.step(epoch_val_loss)

        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch + 1}/{num_epochs}], Train Loss: {epoch_train_loss:.4f}, Val Loss: {epoch_val_loss:.4f}')

    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()

    ###########################################################
    ## Make multistep forecasts & Test error Calculation
    ###########################################################
    model.eval()
    forecasts = []
    for X_batch, _ in val_loader:
        last_input = X_batch[-1].unsqueeze(0)  # Incorrect! Incorrect! Last observation not  getting Selected

    #print('last_input' , last_input)

    direct_input = df.iloc[ -(m_steps + lags) : -(m_steps) , :].values

    direct_input = torch.tensor(direct_input, dtype=torch.float32).reshape_as(last_input)

    current_input = direct_input
    #current_input = last_input.clone().detach().to(device)
    #print('current_input' , current_input)

    with torch.no_grad():
        for _ in range(m_steps):
            #print('step : ' , _ , '\n')

            if exo is not None:
              if _ == 0 :
                #print('current_input' , current_input)
                prediction = model(current_input)
                #print("prediction is: " , prediction)
                exoinput = exo_test.iloc[_, :].values.reshape(1, -1)
                exoinput = torch.tensor(exoinput, dtype=torch.float32).to(device)
                #print('exoinput' , exoinput)
                combined_input = torch.cat(( exoinput ,prediction), dim=1)
                forecasts.append(prediction)
                current_input = torch.cat((current_input[:, df.shape[1]:], combined_input), dim=1)
                #print('current input' , current_input , '\n')
              else:

                  prediction = model(current_input)
                  forecasts.append(prediction)
                  #print('prediction' , prediction)
                  exoinput = exo_test.iloc[_, :].values.reshape(1, -1)
                  exoinput = torch.tensor(exoinput, dtype=torch.float32).to(device)
                  #print('exoinput' , exoinput)
                  combined_input = torch.cat(( exoinput ,prediction), dim=1)
                  #print('combined input' , combined_input)
                  current_input = torch.cat((current_input[:,df.shape[1]:], combined_input), dim=1)
                  #print('current input' , current_input , '\n')

            else:
                  prediction = model(current_input)
                  forecasts.append(prediction)
                  #print('prediction')
                  current_input = torch.cat((current_input[:, df.shape[1]:], prediction), dim=1)

    forecasts = torch.stack(forecasts, dim=1).squeeze(0).cpu().numpy()


    if differencing:
        #print('inverse differencing!')

        initial_values = df.iloc[(-m_steps-1), :].values
        for i in range(forecasts.shape[1]):
            forecasts[:, i] = np.cumsum(forecasts[:, i]) + initial_values[i]

        forecasts_df = pd.DataFrame(forecasts, columns=endo_cols)
    else:
        forecasts_df = pd.DataFrame(forecasts, columns=endo_cols)

    if standardise:
        #print('Inverse of standardising!')
        forecasts = pd.DataFrame(forecasts, columns=endo_cols)
        forecasts_inv = np.zeros_like(forecasts)
        for i, col in enumerate(forecasts.columns):
            forecasts_inv[:, i] = dataset.scalers[col].inverse_transform(forecasts.iloc[:, i].values.reshape(-1, 1)).flatten()
        forecasts_df = pd.DataFrame(forecasts_inv, columns=endo_cols)
    else:
        forecasts_df = pd.DataFrame(forecasts, columns=endo_cols)

    return forecasts_df