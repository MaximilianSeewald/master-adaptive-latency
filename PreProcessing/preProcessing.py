import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import shutil
import os

import sys

sys.path.insert(1, 'C:/Users/Maxim/Documents/GitHub/adaptive-latency/neural-network')
from yoloV5 import detect

print("Starting CSV resampling....")

downSampling = False
testMode = True

colList = ["ID", "timeStamp", "mousePosX", "mousePosY", "mouseLeftButton", "mouseMiddleButton", "mouseRightButton",
           "currentKeys"]
input_data = pd.read_csv("./mouse.csv", usecols=colList, sep=";", low_memory=False)
resampledComplete = pd.DataFrame(
    columns=["ID", "mousePosX", "mousePosY", "mouseLeftButton", "mouseMiddleButton", "mouseRightButton",
             "currentKeys"])

input_data["timeStamp"] = pd.to_datetime(input_data["timeStamp"], unit="ms")
input_data["timeStamp"] = input_data["timeStamp"].round("1L")
input_data["mouseRightButton"] = input_data["mouseRightButton"] .replace({True: 1, False: 0})
input_data["mouseLeftButton"] = input_data["mouseLeftButton"] .replace({True: 1, False: 0})
input_data["mouseMiddleButton"] = input_data["mouseMiddleButton"] .replace({True: 1, False: 0})

where = np.where(input_data.ID != input_data.ID)
A = np.vsplit(input_data, where[0])

tail = True

for data in tqdm(A):
    if tail:
        data.drop(index=data.index[0], axis=0, inplace=True)
    tail = True
    data = data.set_index("timeStamp")
    data.index.name = "timeStamp"
    data["ID"] = data['ID'].replace('_.*', '', regex=True)
    data["ID"] = data["ID"].astype(int)

    resampled = data.groupby(data.index).agg(
        {"mousePosX": "sum", "mousePosY": "sum", "ID": "first", "mouseLeftButton": "first",
         "mouseMiddleButton": "first", "mouseRightButton": "first", "currentKeys": "first"})
    idResampled = resampled.resample('5L').ffill()
    resampled = resampled.resample('5L').mean()

    resampled["ID"] = idResampled["ID"]
    resampled["mouseLeftButton"] = idResampled["mouseLeftButton"]
    resampled["mouseRightButton"] = idResampled["mouseRightButton"]
    resampled["mouseMiddleButton"] = idResampled["mouseMiddleButton"]
    resampled["currentKeys"] = idResampled["currentKeys"]

    resampled["mousePosX"] = resampled["mousePosX"].interpolate().round(2)
    resampled["mousePosY"] = resampled["mousePosY"].interpolate().round(2)

    resampledComplete = resampledComplete.append(resampled, sort=False)

resampledComplete.to_csv(r'preProcessed.csv', sep=';')

print("Starting Image Resampling...")

screenshot_dir = Path('./screenshots')
imageComplete = pd.DataFrame(columns=["timeStamp","ID", "xmin", "ymin", "xmax", "ymax"])
imageComplete.set_index("timeStamp")
imageComplete.index.name = "timeStamp"

screenshots = list(screenshot_dir.iterdir())
for image in tqdm(screenshots):
    name = image.name
    splitName = name.split("_")
    boxes = detect(image)
    if not boxes.empty:
        new_row = {"timeStamp": splitName[2], "ID": splitName[0], "xmin": boxes["xmin"][0],
                   "ymin": boxes["ymin"][0], "xmax": boxes["xmax"][0], "ymax": boxes["ymax"][0]}
    else:
        new_row = {"timeStamp": splitName[2], "ID": splitName[0], "xmin": 0, "ymin": 0, "xmax": 0, "ymax": 0}
    imageComplete = pd.concat([imageComplete, pd.DataFrame([new_row])])

imageComplete.to_csv(r'ImagePreProcessed.csv', sep=';')

print("Starting Upsampling of Images...")

imagesFinished = pd.DataFrame(columns=["ID", "xmin", "ymin", "xmax", "ymax"])
colList = ["timeStamp", "ID", "xmin", "ymin", "xmax", "ymax"]
images = pd.read_csv("./ImagePreProcessed.csv", usecols=colList, sep=";")
images["timeStamp"] = pd.to_datetime(images["timeStamp"], unit="ms")
images["timeStamp"] = images["timeStamp"].round("1L")
images = images.set_index("timeStamp")
images.index.name = "timeStamp"
groupedImages = images.groupby(images.ID)


for data in tqdm(groupedImages):
    data = data[1]
    data = data.resample('5L').ffill()

    imagesFinished = imagesFinished.append(data, sort=False)


imagesFinished.to_csv(r'ImageCompleted.csv', sep=';')

print("Matching Images with Mouse/Keyboard...")

images = pd.read_csv("./ImageCompleted.csv", sep=";", index_col=0)
inputData = pd.read_csv("./preProcessed.csv", index_col=0, sep=";")


drop = []
for i, row in tqdm(images.iterrows()):
    if i not in inputData.index:
        drop.append(i)

for j in tqdm(drop):
    images = images.drop(index=j)

drop = []
for i, row in tqdm(inputData.iterrows()):
    if i not in images.index:
        drop.append(i)

for j in tqdm(drop):
    inputData = inputData.drop(index=j)


images.to_csv(r'ImageFinal.csv', sep=';')
inputData.to_csv(r'CSVFinal.csv', sep=';')

print("Merging Dataframes...")

images = pd.read_csv("./ImageFinal.csv", sep=";", index_col=0)
inputData = pd.read_csv("./CSVFinal.csv", index_col=0, sep=";")

combine = [images, inputData]
result = pd.concat(combine, axis=1)
result.to_csv(r'Final.csv', sep=';')


print("Moving Temp files...")

os.makedirs("temp", exist_ok=True)

shutil.move("CSVFinal.csv", "temp/CSVFinal.csv")
shutil.move("ImageCompleted.csv", "temp/ImageCompleted.csv")
shutil.move("ImageFinal.csv", "temp/mageFinal.csv")
shutil.move("ImagePreProcessed.csv", "temp/ImagePreProcessed.csv")
shutil.move("preProcessed.csv", "temp/preProcessed.csv")

print("Finished")






