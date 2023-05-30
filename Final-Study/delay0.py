import time

import serial
import os
import threading

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import json


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def initArduino():
    global arduinoMouse
    global arduinoKeyboard
    global mouseStarted
    global keyboardStarted

    try:
        arduinoMouse = serial.Serial(port='COM3', baudrate=115200, timeout=.001)
        mouseStarted = True
    except:
        mouseStarted = False
        print("MOUSE NOT FOUND!")

    try:
        arduinoKeyboard = serial.Serial(port='COM5', baudrate=115200, timeout=.001)
        keyboardStarted = True
    except:
        print("KEYBOARD NOT FOUND!")
        keyboardStarted = False


def delay():
    initArduino()
    while isRecording:
            if mouseStarted:
                dataMouse = arduinoMouse.read(100000)
                arduinoMouse.write(str(0).encode() + "\n".encode())
            if keyboardStarted:
                dataKeyboard = arduinoKeyboard.read(100000)
                arduinoKeyboard.write(str(0).encode() + "\n".encode())
            time.sleep(1)
            if not isRecording:
                break


def changeRecording(status):
    global isRecording
    isRecording = status
    arduinoMouse.close()
    arduinoKeyboard.close()


def init():
    global isRecording

    # Cls
    print(chr(27) + "[2J")

    # Set Bools
    isRecording = True


def start():
    init()
    delay()


if __name__ == '__main__':
    start()
