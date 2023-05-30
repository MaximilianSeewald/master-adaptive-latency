import numpy as np
from tensorflow import keras
import pandas as pd
import tensorflow as tf
import json
import warnings
import random
from tensorflow.keras import layers
import datetime
import pathlib
import os
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Reshape, concatenate, Conv2D, Flatten, MaxPooling2D
from tensorflow.keras.layers import BatchNormalization, Dropout, GlobalMaxPooling2D
from keras.callbacks import ModelCheckpoint


warnings.filterwarnings('ignore')

predictTimeMin = 50
predictTimeMax = 150
inputTime = 10
batchSize = 128
epochs = 50
trainSize = 0.8


print("Loading csv Data...")
# Format .csv Data
input_data = pd.read_csv("./Final.csv", sep=";", index_col=[0])
input_data = input_data.drop(columns=["ID", "currentKeys","ID.1"])
input_data = input_data.fillna(0)
input_data.drop(index=input_data.index[0], axis=0, inplace=True)
print(input_data.head())


print("Creating Delay...")
row_count = input_data.count()
random_delay = []
for i in range(row_count[0]):
    random_delay.append(random.randint(predictTimeMin / 5, predictTimeMax / 5) * 5)
input_data.insert(column="delay", value=random_delay, loc=9)



def df_processing(df, window_size=10):
    df_as_np = df.to_numpy()
    X = []
    y = []
    for i in range(len(df_as_np) - (window_size+(int(predictTimeMax/5)))):
        row = [r for r in df_as_np[i:i + window_size]]
        delay = df_as_np[i][9]
        delay = int(delay/5)
        X.append(row)
        label = [df_as_np[i + window_size + delay][4], df_as_np[i+window_size+ delay][5],df_as_np[i+window_size+ delay][6]]
        y.append(label)
    return np.array(X), np.array(y)

x,y = df_processing(input_data)

trainsize = int(trainSize * len(x))
valSize = (len(input_data)-trainsize)/2
valSize = int(trainsize+valSize)
x_train, y_train = x[0:trainsize], y[0:trainsize]
x_val, y_val = x[trainsize:valSize], y[trainsize:valSize]
x_test, y_test = x[valSize:], y[valSize:]



input_train = x_train
output_train = y_train
output_val = y_val
input_val = x_val

print("Start Training...")
inputCSV = layers.Input(shape=(10,10))
csvModel = keras.layers.Conv1D(filters=64, kernel_size=2, activation='relu')(inputCSV)
csvModel = keras.layers.Conv1D(filters=64, kernel_size=6, activation='relu')(csvModel)
csvModel = keras.layers.MaxPool1D(pool_size=2)(csvModel)
csvModel = keras.layers.Flatten()(csvModel)
csvModel = keras.layers.RepeatVector(10)(csvModel)
csvModel = keras.layers.LSTM(200, activation='relu')(csvModel)
csvModel = keras.layers.Dense(100,activation='relu')(csvModel)
csvModel = keras.layers.Dense(3)(csvModel)
model = keras.Model(inputCSV, csvModel)

optimizer = tf.keras.optimizers.Adam(learning_rate=0.1, clipnorm=1.)
reduceLR = tf.keras.callbacks.ReduceLROnPlateau(monitor='mae', factor=0.1, min_lr=1e-5, patience=2, verbose=1)
lossFunction = tf.keras.losses.MeanSquaredError()
model.compile(loss=lossFunction, optimizer=optimizer, metrics=['mae'])
model.summary()
filepath = "./savedLSTMCNNModel/weights-improvement-{epoch:02d}-{mae:.2f}.hdf5"
checkpoint = ModelCheckpoint(filepath, monitor='mae', verbose=1, save_best_only=False, mode='min')
log_dir = "./savedLSTMCNNModel/logs/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)
callbacks = [checkpoint, reduceLR, tensorboard_callback]

model.fit(input_train, output_train, epochs=epochs, callbacks=callbacks, validation_data=(input_val, output_val), batch_size=batchSize)

eval = model.evaluate(x_test,y_test,batch_size=batchSize)
json = json.dumps(dict(zip(model.metrics_names, eval)))
f = open("LSTMCNN.json","w")
f.write(json)
f.close()

print("Final Predict...")
predict = model.predict(input_val[8740:8741])
print("Prediction: " + str(predict))
print("Real Value: " + str(output_val[8740:8741]))

model.save('savedLSTMCNNModel')
