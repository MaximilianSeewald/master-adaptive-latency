import threading
from multiprocessing import Process, Queue
from copy import deepcopy
from pynput.mouse import Button, Controller
import numpy as np
import pandas as pd
import serial
import time
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import d3dshot
import cv2
import pygame
import json
import sys
import tensorflow as tf


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def startRecording():
    global d
    d = d3dshot.create(capture_output="numpy", frame_buffer_size=60)
    d.display = d.displays[0]
    d.capture(target_fps=30)
    time.sleep(0.1)


def imageCaptureLoop(input, output):
    startRecording()
    clock = pygame.time.Clock()
    isRecording = True
    while isRecording:
        if not input.empty():
            isRecording = input.get()
        newFrame = d.get_latest_frame()
        newFrame = cv2.resize(newFrame, dsize=(848, 480), interpolation=cv2.INTER_CUBIC)
        newFrame = cv2.cvtColor(newFrame, cv2.COLOR_BGR2RGB)
        tempFrame = newFrame
        imageChanged = True
        output.put((isRecording, tempFrame, imageChanged))
        clock.tick(30)


def detectImage(input, output):
    sys.path.insert(1, 'C:/Users/Maxim/Documents/GitHub/adaptive-latency/neural-network')
    from yoloV5 import detect
    imageChanged = False
    isRecording = True
    while isRecording:
        if not input.empty():
            isRecording, tempFrame, imageChanged = input.get()
        if imageChanged:
            boxes = detect(tempFrame)
            if not boxes.empty:
                boxRow = [boxes["xmin"][0], boxes["ymin"][0], boxes["xmax"][0], boxes["ymax"][0]]
            else:
                boxRow = [0, 0, 0, 0]
            output.put((boxRow, isRecording))
            imageChanged = False


def initArduino():
    global arduinoMouse
    global arduinoKeyboard
    global mouseStarted
    global keyboardStarted

    try:
        arduinoMouse = serial.Serial(port='COM3', baudrate=115200, timeout=.1)
        mouseStarted = True
    except:
        mouseStarted = False
        arduinoMouse = 0
        print("MOUSE NOT FOUND!")

    try:
        arduinoKeyboard = serial.Serial(port='COM5', baudrate=115200, timeout=.1)
        keyboardStarted = True
    except:
        print("KEYBOARD NOT FOUND!")
        arduinoKeyboard = 0
        keyboardStarted = False


def mouseCaptureLoop(input, output, delayInput):
    global isRecording
    initArduino()
    clock = pygame.time.Clock()
    delayLoop = threading.Thread(target=delay, args=(delayInput,))
    delayLoop.start()
    isRecording = True
    mouseArray = []
    mouseMiddleButton = 0
    mouseRightButton = 0
    mouseLeftButton = 0
    while isRecording:
        if not input.empty():
            isRecording = input.get()
        if mouseStarted:
            dataMouse = arduinoMouse.readline().decode('utf-8').rstrip()
            mouse = str(dataMouse).split(":")
            if len(mouse) > 1:
                if mouse[0] == "MOVE":
                    x = mouse[1]
                    y = mouse[2]
                else:
                    x = 0
                    y = 0
                    button = mouse[1]
                    if button == "0":
                        mouseLeftButton = 0
                    if button == "1":
                        mouseLeftButton = 1
                    if button == "2":
                        mouseRightButton = 0
                    if button == "3":
                        mouseRightButton = 1
                    if button == "4":
                        mouseMiddleButton = 0
                    if button == "5":
                        mouseMiddleButton = 1
            else:
                x = 0
                y = 0

            currtime = round(time.time() * 1000)
        else:
            x = 0
            y = 0
            currtime = round(time.time() * 1000)
        clock.tick(200)
        tempArray = [currtime, x, y, mouseLeftButton, mouseMiddleButton, mouseRightButton]
        mouseArray.append(tempArray)
        if mouseArray[0][0] < (round(time.time() * 1000) - 100):
            mouseArray.pop(0)
        output.put((mouseArray))
    delayLoop.join()


def delay(output):
    smoothingDelay = 90
    with open("delay150.txt", "r") as f:
        delayArray = json.load(f)
    while isRecording:
        for i in range(len(delayArray)):
            if mouseStarted:
                arduinoMouse.write(str(delayArray[i] - smoothingDelay).encode() + "\n".encode())
            if keyboardStarted:
                dataKeyboard = arduinoKeyboard.read(100000)
                arduinoKeyboard.write(str(delayArray[i] - smoothingDelay).encode() + "\n".encode())
            output.put(delayArray[i])
            time.sleep(1)
            if not isRecording:
                break
    arduinoMouse.close()
    arduinoKeyboard.close()


def interpolateMouse(inputBox, inputMouse, output):
    global predictArray
    isRecording = True
    boxRow = []
    mouseA = []
    while isRecording:
        if not inputBox.empty():
            boxRow, isRecording = inputBox.get()
        if not inputMouse.empty():
            mouseA = inputMouse.get()
        tempArray = deepcopy(mouseA)
        tempRow = deepcopy(boxRow)
        if len(tempRow) > 0 and len(tempArray) > 1:
            for i in range(len(tempArray)):
                tempArray[i].append(tempRow[0])
                tempArray[i].append(tempRow[1])
                tempArray[i].append(tempRow[2])
                tempArray[i].append(tempRow[3])
            df = pd.DataFrame(tempArray)
            df = df.astype('float64')
            df = df.set_index(0)
            df.index = pd.to_datetime(df.index, unit="ms")
            df.index = df.index.round("1L")
            resampled = df.groupby(df.index).agg(
                {1: "sum", 2: "sum", 3: "first", 4: "first",
                 5: "first", 6: "first", 7: "first", 8: "first", 9: "first"})
            idResampled = resampled.resample('5L').ffill()
            resampled = resampled.resample('5L').mean()
            resampled.iloc[1:, [2, 3, 4, 5, 6, 7, 8]] = idResampled.iloc[1:, [2, 3, 4, 5, 6, 7, 8]]
            resampled = resampled.iloc[1:]
            resampled.iloc[:, [0]] = resampled.iloc[:, [0]].interpolate().round(2)
            resampled.iloc[:, [1]] = resampled.iloc[:, [1]].interpolate().round(2)

            result = resampled.tail(10)
            result = result.fillna(0)
            result = result.values.flatten()
            output.put(result)


def predictLoop():
    model = tf.keras.models.load_model('savedDenseModel')
    start = round(time.time() * 1000)
    isPressed = False
    # Create Virt Mouse
    mouse = Controller()
    arrayPredict = []
    currentDelay = 0
    while isRecording:
        if not finalQue.empty():
            arrayPredict = finalQue.get()
        if not delayQue.empty():
            currentDelay = delayQue.get()
        if len(arrayPredict) == 90:
            arrayPredict = np.insert(arrayPredict, 9, currentDelay)
            predict = model(arrayPredict)
            predict = np.around(predict)
            smoothedX = predict[0][0]
            smoothedY = predict[0][0]
            if predict[0][2] == 1:
                mouse.press(Button.left)
                isPressed = True
            if predict[0][2] == 0 and isPressed:
                mouse.release(Button.left)
                isPressed = False
            mouse.move(predict[0][0] - smoothedX, predict[0][1] - smoothedY)
            start = round(time.time() * 1000)
    imageCaptureQue.put(False)
    mouseCapQue.put(False)


def changeRecording(status):
    global isRecording
    isRecording = status


def init():
    global clock
    global isRecording
    global predictQue
    global boxQue
    global mouseQue
    global finalQue
    global imageCaptureQue
    global mouseCapQue
    global delayQue

    # Cls
    print(chr(27) + "[2J")

    # Set Bools
    isRecording = True

    predictQue = Queue(maxsize=1)
    boxQue = Queue(maxsize=1)
    finalQue = Queue(maxsize=1)
    mouseQue = Queue(maxsize=1)
    imageCaptureQue = Queue(maxsize=1)
    mouseCapQue = Queue(maxsize=1)
    delayQue = Queue(maxsize=1)

    mouseCapQue.put(isRecording)
    imageCaptureQue.put(isRecording)

    # Create Clock
    clock = pygame.time.Clock()


def start():
    init()
    detectLoop = Process(target=detectImage, args=(predictQue, boxQue), )
    detectLoop.start()
    interpolateLoop = Process(target=interpolateMouse, args=(boxQue, mouseQue, finalQue), )
    interpolateLoop.start()
    imageCap = Process(target=imageCaptureLoop, args=(imageCaptureQue, predictQue), )
    imageCap.start()
    mouseCap = Process(target=mouseCaptureLoop, args=(mouseCapQue, mouseQue, delayQue), )
    mouseCap.start()
    predictLoop()
    detectLoop.terminate()
    interpolateLoop.terminate()
    imageCap.terminate()
    mouseCap.terminate()


if __name__ == '__main__':
    start()
