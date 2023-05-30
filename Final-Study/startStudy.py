import os
import time
import threading
import random
import string
from win10toast import ToastNotifier
import webbrowser
from pynput import keyboard
import pyautogui
import shutil

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import delay100
import delay150
import delay0
import prediction100
import prediction150


def onKeyboardClicked(key):
    global hasPressed
    if key == keyboard.Key.f10:
        hasPressed = True


def timerLoop():
    timedDelay = time.time() + runtime
    while time.time() < timedDelay:
        print(timedDelay-time.time())
        time.sleep(5)


def startNoDelay():
    loop = threading.Thread(target=delay0.start)
    loop.start()
    timerLoop()
    delay0.changeRecording(False)
    loop.join()


def startPrediction100():
    loop = threading.Thread(target=prediction100.start)
    loop.start()
    timerLoop()
    prediction100.changeRecording(False)
    loop.join()


def startPrediction150():
    loop = threading.Thread(target=prediction150.start)
    loop.start()
    timerLoop()
    prediction150.changeRecording(False)
    loop.join()


def startDelay100():
    loop = threading.Thread(target=delay100.start)
    loop.start()
    timerLoop()
    delay100.changeRecording(False)
    loop.join()


def startDelay150():
    loop = threading.Thread(target=delay150.start)
    loop.start()
    timerLoop()
    delay150.changeRecording(False)
    loop.join()


def openQuestionnaire():
    global hasPressed
    hasPressed = False
    print("Sending User to GoogleForms Link")
    url = f"https://docs.google.com/forms/d/e/1FAIpQLSevWtgoMaqV0KlXHzl2DiSLLZ4RDLyuCPCjN_V35sxoxPxlIw/viewform?usp=pp_url&entry.1065745336={userID}"
    webbrowser.open_new(url)
    while not hasPressed:
        time.sleep(1)
    hasPressed = False


def reopen(run):
    global hasPressed
    hasPressed = False
    toast = ToastNotifier()
    toast.show_toast("Study", "Zeit vorbei!", duration=10, threaded=True)
    print("Reopen Browser")
    pyautogui.getWindowsWithTitle("Google Chrome")[0].minimize()
    pyautogui.getWindowsWithTitle("Google Chrome")[0].maximize()
    os.makedirs( userID + '\\' + str(run))
    time.sleep(7)
    shutil.copy('G:\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\csgo\\backup_round00.txt',
                userID + '\\' + str(run))
    print("Copied Files")
    while not hasPressed:
        time.sleep(1)
    hasPressed = False
    print("Running")


def init():
    global runtime
    global userID
    global hasPressed

    keyboardListener = keyboard.Listener(on_press=onKeyboardClicked)
    keyboardListener.start()

    userID = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    # Cls
    print(chr(27) + "[2J")

    runtime = 60*2

    hasPressed = False
    os.makedirs(userID)


if __name__ == '__main__':
    init()
    openQuestionnaire()
    startNoDelay()
    reopen(1)
    startDelay100()
    reopen(2)
    startPrediction100()
    reopen(3)
    startDelay150()
    reopen(4)
    startPrediction150()
    reopen(5)
