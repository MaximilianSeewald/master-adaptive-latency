import time
import os
import pygame
from pynput import mouse
from pynput import keyboard
import csv
from pathlib import Path
import d3dshot
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import cv2


def startRecording():
    d.capture(target_fps=60)
    time.sleep(0.1)


def produceCSVQue(pos, lastTime, ic, cc):
    csvQueue.put([pos, lastTime, ic, cc])


def produceImageCaptureQueue(frame, posTime, ic):
    imageQueue.put([frame, posTime, ic])


def getFrame(ic):
    frame = d.get_latest_frame()
    posTime = int(round(time.time() * 1000))
    imageTimeStamps.append(posTime)
    produceImageCaptureQueue(frame, posTime, ic)


def getMousePos():
    pos = mouse.Controller().position
    return pos


def onMouseClicked(x, y, button, pressed):
    global mouseLeftButton
    global mouseRightButton
    global mouseMiddleButton
    if str(button) == "Button.left":
        mouseLeftButton = pressed
    if str(button) == "Button.right":
        mouseRightButton = pressed
    if str(button) == "Button.middle":
        mouseMiddleButton = pressed


def onKeyboardClicked(key):
    global currentKeysPressed
    global isRecording
    if key not in currentKeysPressed:
        currentKeysPressed.append(key)
    if key == keyboard.Key.pause:
        isRecording = False


def onKeyboardReleased(key):
    global currentKeysPressed
    if key in currentKeysPressed:
        currentKeysPressed.remove(key)


def saveFrame(image, posTime, id):
    image = cv2.resize(image, dsize=(848, 480), interpolation=cv2.INTER_CUBIC)
    im_bgr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    cv2.imwrite("screenshots/" + str(posTime) + "_{0}_screenshot.jpg".format(str(id)), im_bgr)


def writeToCSV(mousePos, time, imageCounter, counter):
    with open("preStudyDataWithImages.csv", mode='a', newline='') as csv_file:
        csvWriter = csv.writer(csv_file, delimiter=';')
        id = str(imageCounter) + "_" + str(counter)
        csvWriter.writerow([id, time, mousePos[0], mousePos[1], mouseLeftButton, mouseMiddleButton, mouseRightButton,
                            currentKeysPressed])
        csv_file.close()


def startSavingImages():
    global isSavingImages
    while isSavingImages:
        if not imageQueue.empty():
            i = imageQueue.get()
            saveFrame(i[0], i[1], i[2])
        else:
            if not isRecording:
                isSavingImages = False
        time.sleep(0.01)
    print("Images Saved")


def startWritingCsv():
    global isSavingCSV
    while isSavingCSV:
        if not csvQueue.empty():
            i = csvQueue.get()
            writeToCSV(i[0], i[1], i[2], i[3])
        else:
            if not isRecording:
                isSavingCSV = False
    print("CSV Saved")


def init():
    # Vars
    global isRecording
    global mouseLeftButton
    global mouseRightButton
    global mouseMiddleButton
    global currentKeysPressed
    global d
    global imageCounter
    global clock
    global imageTimeStamps
    global isSavingCSV
    global isSavingImages
    global imageQueue
    global csvQueue

    imageQueue = Queue()
    csvQueue = Queue()

    # Set Bools to Default Value
    isRecording = True
    isSavingCSV = True
    isSavingImages = True
    mouseMiddleButton = False
    mouseRightButton = False
    mouseLeftButton = False

    # Set Ints
    imageCounter = 0

    # Set Arrays
    currentKeysPressed = []
    imageTimeStamps = []

    # Create Image Path
    Path("screenshots").mkdir(parents=True, exist_ok=True)

    # Init Capture
    d = d3dshot.create(capture_output="numpy", frame_buffer_size=60)
    d.display = d.displays[0]

    # Create Clock
    clock = pygame.time.Clock()

    # Start Listeners
    mouseListener = mouse.Listener(on_click=onMouseClicked)
    mouseListener.start()
    keyboardListener = keyboard.Listener(on_press=onKeyboardClicked, on_release=onKeyboardReleased)
    keyboardListener.start()

    # Start Image Capture
    startRecording()

    # Create CSV
    if not os.path.exists("preStudyDataWithImages.csv"):
        with open("preStudyDataWithImages.csv", mode='a', newline='') as csv_file:
            csvWriter = csv.writer(csv_file, delimiter=';')
            csvWriter.writerow(["ID", "timeStamp", "mousePosX", "mousePosY", "mouseLeftButton", "mouseMiddleButton",
                                "mouseRightButton", "currentKeysPressed"])

    # Start Queue Getters
    process = []
    with ThreadPoolExecutor(max_workers=20) as executer:
        process.append(executer.submit(startWritingCsv))
        process.append(executer.submit(startSavingImages))
        # Start Loop
        loop()


def loop():
    global imageCounter
    clickCounter = 0
    lastTime = 0

    while isRecording:
        currentTime = int(round(time.time() * 1000))
        if (lastTime + 1) <= currentTime:
            lastTime = currentTime
            mousePos = getMousePos()
            if clickCounter == 5:
                getFrame(imageCounter)
                imageCounter += 1
                clickCounter = 0
            clickCounter += 1
            produceCSVQue(mousePos, lastTime, imageCounter, clickCounter)
        clock.tick(1000)


if __name__ == '__main__':
    init()
