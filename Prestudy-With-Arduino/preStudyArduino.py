import threading
import serial
import csv
import time
import os
import d3dshot
import cv2
from pathlib import Path
import pygame
from queue import Queue

d = d3dshot.create(capture_output="numpy", frame_buffer_size=60)

try:
    arduinoMouse = serial.Serial(port='COM3', baudrate=115200, timeout=.1)
    mouseStarted = True
except:
    mouseStarted = False
    print("MOUSE NOT FOUND!")

try:
    arduinoKeyboard = serial.Serial(port='COM5', baudrate=115200, timeout=.1)
    keyboardStarted = True
except:
    print("KEYBOARD NOT FOUND!")
    keyboardStarted = False


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def startRecording():
    d.capture(target_fps=60)
    time.sleep(0.1)


def imageCapture():
    global isRecording
    global imageCounter
    global clock

    while isRecording:
            frame = d.get_latest_frame()
            posTime = int(round(time.time() * 1000))
            image = cv2.resize(frame, dsize=(848, 480), interpolation=cv2.INTER_CUBIC)
            im_bgr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            cv2.imwrite("screenshots/" + str(posTime) + "_{0}_screenshot.jpg".format(str(imageCounter)), im_bgr)
            imageCounter = imageCounter + 1
            clock.tick(60)


def csvWrite():
    global imageRate
    global csvCounter
    global isRecording
    global csvQueue
    global csvSaved

    while not csvSaved:
        if not csvQueue.empty():
            i = csvQueue.get()
            csvCounter = csvCounter + 1
            with open("preStudyData.csv", mode='a', newline='') as csv_file:
                csvWriter = csv.writer(csv_file, delimiter=';')
                id = str(csvCounter)
                csvWriter.writerow(
                    [id, i[2], i[0], i[1], mouseLeftButton, mouseMiddleButton, mouseRightButton, currentKeysPressed])
                csv_file.close()
        else:
            if not isRecording:
                csvSaved = True


def loop():
    global mouseLeftButton
    global mouseRightButton
    global mouseMiddleButton
    global isRecording

    print("Capturing Started!")
    while isRecording:
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
                        mouseLeftButton = False
                    if button == "1":
                        mouseLeftButton = True
                    if button == "2":
                        mouseRightButton = False
                    if button == "3":
                        mouseRightButton = True
                    if button == "4":
                        mouseMiddleButton = False
                    if button == "5":
                        mouseMiddleButton = True
            else:
                x = 0
                y = 0
        else:
            time.sleep(0.03)
            x = 0
            y = 0
        currentTime = int(round(time.time() * 1000))
        csvQueue.put([y, x, currentTime])


def keyboardThread():
    global currentKeysPressed
    global isRecording
    while isRecording:
        dataKeyboard = arduinoKeyboard.readline().decode('utf-8').rstrip()
        key = str(dataKeyboard).split(":")
        if len(key) > 1:
            if key[0] == "KeyDown":
                currentKeysPressed.append(key[1])
                if key[1] == "208":
                    isRecording = False
            else:
                if key[1] in currentKeysPressed:
                    currentKeysPressed.remove(key[1])
        currentTime = int(round(time.time() * 1000))
        csvQueue.put([0, 0, currentTime])

    kt.do_run = False
    imageCap.do_run = False
    d.stop()

    while not csvSaved:
        time.sleep(0.1)
    inputAgain = input("Run Again: ")

    if inputAgain == 'y':
        init()


def init():
    global mouseLeftButton
    global mouseRightButton
    global mouseMiddleButton
    global currentKeysPressed
    global csvCounter
    global d
    global isRecording
    global kt
    global imageCap
    global imageCounter
    global csvQueue
    global csvSaved
    global clock

    # Cls
    print(chr(27) + "[2J")

    # Set Bools
    mouseMiddleButton = False
    mouseRightButton = False
    mouseLeftButton = False
    isRecording = True
    csvSaved = False

    # Set Arrays
    currentKeysPressed = []

    # Set Int
    csvCounter = 0
    imageCounter = 2

    # Queues
    csvQueue = Queue()

    # Init Capture
    d.display = d.displays[0]

    # Create Clock
    clock = pygame.time.Clock()

    # Create Image Path
    Path("screenshots").mkdir(parents=True, exist_ok=True)

    # Start Image Capture
    startRecording()

    if not os.path.exists("preStudyData.csv"):
        with open("preStudyData.csv", mode='a', newline='') as csv_file:
            csvWriter = csv.writer(csv_file, delimiter=';')
            csvWriter.writerow(["ID", "timeStamp", "mousePosX", "mousePosY", "mouseLeftButton", "mouseMiddleButton",
                                "mouseRightButton", "currentKeys"])
    inputDelay = input("Enter Delay: ")
    print("Input recieved: " + str(inputDelay))
    if mouseStarted:
        arduinoMouse.write(inputDelay.encode() + '\n'.encode())
    if keyboardStarted:
        arduinoKeyboard.write(inputDelay.encode() + '\n'.encode())
        kt = threading.Thread(target=keyboardThread)
        kt.start()
    imageCap = threading.Thread(target=imageCapture)
    imageCap.start()
    cw = threading.Thread(target=csvWrite)
    cw.start()
    loop()


init()
