import time
from pynput import mouse
from pynput import keyboard
import csv
import os
import win32api


def getMousePos():
    global lastX
    global lastY
    pos = win32api.GetCursorPos()
    x = pos[0] - lastX
    y = pos[1] - lastY
    lastX = pos[0]
    lastY = pos[1]
    return [x,y]


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
    global isRecording
    global currentKeysPressed
    if key not in currentKeysPressed:
        currentKeysPressed.append(key)
    if key == keyboard.Key.pause:
        isRecording = False


def onKeyboardReleased(key):
    global currentKeysPressed
    if key in currentKeysPressed:
        currentKeysPressed.remove(key)


def writeToCSV(mousePos, time, counter):
    with open("preStudyData.csv", mode='a', newline='') as csv_file:
        csvWriter = csv.writer(csv_file, delimiter=';')
        id = str(counter)
        csvWriter.writerow([id, time, mousePos[0], mousePos[1], mouseLeftButton, mouseMiddleButton, mouseRightButton,
                            currentKeysPressed])
        csv_file.close()


def init():
    # Vars
    global isRecording
    global mouseLeftButton
    global mouseRightButton
    global mouseMiddleButton
    global currentKeysPressed
    global csvCounter
    global lastX
    global lastY

    # Set Bools to Default Value
    isRecording = True
    mouseMiddleButton = False
    mouseRightButton = False
    mouseLeftButton = False

    # Set Ints
    csvCounter = 0
    lastX = 0
    lastY = 0

    # Set Arrays
    currentKeysPressed = []

    # Start Listeners
    mouseListener = mouse.Listener(on_click=onMouseClicked)
    mouseListener.start()
    keyboardListener = keyboard.Listener(on_press=onKeyboardClicked, on_release=onKeyboardReleased)
    keyboardListener.start()

    if not os.path.exists("preStudyData.csv"):
        with open("preStudyData.csv", mode='a', newline='') as csv_file:
            csvWriter = csv.writer(csv_file, delimiter=';')
            csvWriter.writerow(["ID", "timeStamp", "mousePosX", "mousePosY", "mouseLeftButton", "mouseMiddleButton",
                                "mouseRightButton", "currentKeysPressed"])

    # Start Loop
    loop()


def loop():
    global csvCounter

    while isRecording:
        currentTime = int(round(time.time() * 1000))
        mousePos = getMousePos()

        # write to CSV
        writeToCSV(mousePos, currentTime, csvCounter)

        # Adjust Counter
        csvCounter = csvCounter + 1
        time.sleep(0.01)


init()
