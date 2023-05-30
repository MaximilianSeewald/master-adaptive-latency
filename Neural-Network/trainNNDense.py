import numpy as np
from tensorflow import keras
import pandas as pd
import tensorflow as tf
from tqdm import tqdm
import time
import warnings
import json
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
colList = ["xmin","ymin","xmax","ymax","mousePosX","mousePosY","mouseLeftButton","mouseMiddleButton","mouseRightButton"]
input_data = pd.read_csv("./Final.csv", sep=";",usecols=colList)
input_data = input_data.fillna(0)
input_data.drop(index=input_data.index[0], axis=0, inplace=True)
print(input_data.head())



print("Creating Delay...")
row_count = input_data.count()
random_delay = []
for i in range(row_count[0]):
    random_delay.append(random.randint(predictTimeMin / 5, predictTimeMax / 5) * 5)
input_data.insert(column="delay", value=random_delay, loc=9)
output_data = pd.DataFrame(
    columns=["mousePosX", "mousePosY", "mouseLeftButton"])
xPosList = []
yPosList = []
rMouseList = []
mMouseList = []
lMouseList = []
failCounter = 0

for index, row in tqdm(input_data.iterrows()):
    shift = row["delay"]
    shift = shift / 5
    try:
        xPos = input_data.iloc[[int(index + shift)]]["mousePosX"]
        yPos = input_data.iloc[[int(index + shift)]]["mousePosY"]
        rMouse = input_data.iloc[[int(index + shift)]]["mouseRightButton"]
        mMouse = input_data.iloc[[int(index + shift)]]["mouseMiddleButton"]
        lMouse = input_data.iloc[[int(index + shift)]]["mouseLeftButton"]
        xPos = xPos.values[0]
        yPos = yPos.values[0]
        rMouse = rMouse.values[0]
        mMouse = mMouse.values[0]
        lMouse = lMouse.values[0]
    except:
        xPos = 0
        yPos = 0
        rMouse = 0
        mMouse = 0
        lMouse = 0
        failCounter = failCounter + 1
    xPosList.append(xPos)
    yPosList.append(yPos)
    rMouseList.append(rMouse)
    lMouseList.append(lMouse)
    mMouseList.append(mMouse)

print(failCounter)
s1 = pd.Series(xPosList)
s2 = pd.Series(yPosList)
s3 = pd.Series(rMouseList)
s4 = pd.Series(mMouseList)
s5 = pd.Series(lMouseList)
output_data["mousePosX"] = s1.values
output_data["mousePosY"] = s2.values
#output_data["mouseRightButton"] = s3.values
#output_data["mouseMiddleButton"] = s4.values
output_data["mouseLeftButton"] = s5.values

print("Adding more Input Rows...")
# Add more input rows
for i in range(inputTime-1):
    counter = i + 1
    input_data["mousePosX" + str(counter)] = input_data["mousePosX"].shift(counter, fill_value=0).astype(int)
    input_data["mousePosY" + str(counter)] = input_data["mousePosY"].shift(counter, fill_value=0).astype(int)
    input_data["xmin" + str(counter)] = input_data["xmin"].shift(counter, fill_value=0).astype(float)
    input_data["ymin" + str(counter)] = input_data["ymin"].shift(counter, fill_value=0).astype(float)
    input_data["xmax" + str(counter)] = input_data["xmax"].shift(counter, fill_value=0).astype(float)
    input_data["ymax" + str(counter)] = input_data["ymax"].shift(counter, fill_value=0).astype(float)
    input_data["mouseRightButton" + str(counter)] = input_data["mouseRightButton"].shift(counter, fill_value=0).astype(int)
    input_data["mouseLeftButton" + str(counter)] = input_data["mouseLeftButton"].shift(counter, fill_value=0).astype(int)
    input_data["mouseMiddleButton" + str(counter)] = input_data["mouseMiddleButton"].shift(counter, fill_value=0).astype(int)

print("Checking for NaN...")
input_data = input_data.fillna(0)
output_data = output_data.fillna(0)
input_data = input_data.values
output_data = output_data.values

print("Split Data...")
# Split train and valdidation
trainsize = int(trainSize * len(input_data))
valSize = (len(input_data)-trainsize)/2
valSize = int(trainsize+valSize)
input_train = input_data[0:trainsize]
input_val = input_data[trainsize:valSize]
input_test = input_data[valSize:]
output_train = output_data[0:trainsize]
output_val = output_data[trainsize:valSize]
output_test = output_data[valSize:]

print(input_data.shape[1])

print("Start Training...")
inputCSV = layers.Input(shape=[input_data.shape[1],])
csvModel = keras.layers.Normalization(axis=None)(inputCSV)
csvModel = layers.Dense(64, activation='relu')(csvModel)
csvModel = layers.Dense(32, activation='sigmoid')(csvModel)
csvModel = keras.layers.Dropout(.4)(csvModel)
csvModel = layers.Dense(16, activation='relu')(csvModel)
csvModel = layers.Dense(8, activation='linear')(csvModel)
csvModel = keras.layers.Dropout(.2)(csvModel)
csvModel = layers.Dense(3)(csvModel)
model = keras.Model(inputCSV, csvModel)

optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3, clipnorm=1.)
reduceLR = tf.keras.callbacks.ReduceLROnPlateau(monitor='mae', factor=0.1, min_lr=1e-5, patience=2, verbose=1)
lossFunction = tf.keras.losses.MeanSquaredError()
model.compile(loss=lossFunction, optimizer=optimizer, metrics=['mae'])
model.summary()
filepath = "./savedDenseModel/weights-improvement-{epoch:02d}-{mae:.2f}.hdf5"
checkpoint = ModelCheckpoint(filepath, monitor='mae', verbose=1, save_best_only=False, mode='min')
log_dir = "./savedDenseModel/logs/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)
callbacks = [checkpoint, reduceLR, tensorboard_callback]

model.fit(input_train, output_train, epochs=epochs, callbacks=callbacks, validation_data=(input_val, output_val), batch_size=batchSize)
eval = model.evaluate(input_test,output_test,batch_size=batchSize)
json = json.dumps(dict(zip(model.metrics_names, eval)))
f = open("dense.json","w")
f.write(json)
f.close()


print("Final Predict...")
start = round(time.time() * 1000)
predict = model(input_val[8740:8741])
predict = np.around(predict)
print(round(time.time() * 1000) - start)
print("Prediction: " + str(predict))
print("Real Value: " + str(output_val[8740:8741]))

model.save('savedDenseModel')
