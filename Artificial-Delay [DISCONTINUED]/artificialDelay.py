import time
import pyWinhook
import pythoncom
import win32api
import win32process, win32con
from pynput.mouse import Button, Controller
import ctypes
from ctypes import wintypes
import multiprocessing

user32 = ctypes.WinDLL('user32', use_last_error=True)
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
MAPVK_VK_TO_VSC = 0
wintypes.ULONG_PTR = wintypes.WPARAM


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR))

    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk,
                                                 MAPVK_VK_TO_VSC, 0)


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT))

    _anonymous_ = ("_input",)
    _fields_ = (("type", wintypes.DWORD),
                ("_input", _INPUT))


LPINPUT = ctypes.POINTER(INPUT)


def PressKey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))


def ReleaseKey(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD,
              ki=KEYBDINPUT(wVk=hexKeyCode,
                            dwFlags=KEYEVENTF_KEYUP))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))


def init():
    global hookManager
    global delayedTime
    global mouseRecordDelay

    hookManager = pyWinhook.HookManager()
    delayedTime = 0.15
    mouseRecordDelay = 0.002


def MouseHandler(event):
    global lastMousePosTime
    currenttime = time.time()

    if lastMousePosTime + mouseRecordDelay < currenttime:
        if event.Injected != 0:
            return True
        pos = event.Position
        x, y = win32api.GetCursorPos()
        xp = pos[0] - x
        yp = pos[1] - y
        customEvent = [xp, yp, currenttime, 0, 0, 1]
        eventQueue.put(customEvent)
        lastMousePosTime = currenttime
    return False


def KeyboardHandlerDown(event):
    if event.Injected != 0:
        return True
    currenttime = time.time()
    customEvent = [0, 0, currenttime, event.KeyID, 0, 2]
    eventQueue.put(customEvent)
    return False


def KeyboardHandlerUp(event):
    if event.Injected != 0:
        return True
    currenttime = time.time()
    customEvent = [0, 0, currenttime, event.KeyID, 0, 3]
    eventQueue.put(customEvent)
    return False


def MouseButtons(event):
    if event.Injected == 1:
        return True
    currenttime = time.time()
    if event.Message == 513:
        customEvent = [0, 0, currenttime, 0, 1, 0]
    elif event.Message == 514:
        customEvent = [0, 0, currenttime, 0, 2, 0]
    elif event.Message == 516:
        customEvent = [0, 0, currenttime, 0, 3, 0]
    elif event.Message == 517:
        customEvent = [0, 0, currenttime, 0, 4, 0]
    elif event.Message == 519:
        customEvent = [0, 0, currenttime, 0, 5, 0]
    elif event.Message == 520:
        customEvent = [0, 0, currenttime, 0, 6, 0]
    eventQueue.put(customEvent)
    return False


def MouseWheel(event):
    global positions
    if event.Injected == 1:
        return True
    currenttime = time.time()
    if event.Wheel == 1:
        customEvent = [0, 0, currenttime, 0, 7, 0]
    elif event.Wheel == -1:
        customEvent = [0, 0, currenttime, 0, 8, 0]
    eventQueue.put(customEvent)
    return False


def queueThread(queue):
    global eventQueue
    mouse = Controller()
    eventQueue = queue
    while True:
        print(eventQueue.qsize())
        pos = eventQueue.get(block=True)
        while (time.time() - delayedTime) < pos[2]:
            time.sleep(0.01)
        if pos[5] == 1:
            mouse.move(pos[0], pos[1])
        if pos[4] == 1:
            mouse.press(Button.left)
        if pos[4] == 2:
            mouse.release(Button.left)
        if pos[4] == 3:
            mouse.press(Button.right)
        if pos[4] == 4:
            mouse.release(Button.right)
        if pos[4] == 7:
            mouse.scroll(0, 1)
        if pos[4] == 8:
            mouse.scroll(0, -1)
        if pos[4] == 5:
            mouse.press(Button.middle)
        if pos[4] == 6:
            mouse.release(Button.middle)
        if pos[5] == 2:
            hex_str = hex(pos[3])
            hex_int = int(hex_str, 16)
            PressKey(hex_int)
        if pos[5] == 3:
            hex_str = hex(pos[3])
            hex_int = int(hex_str, 16)
            ReleaseKey(hex_int)


def hookThread(queue):
    global eventQueue
    global lastMousePosTime
    lastMousePosTime = 0
    eventQueue = queue
    hookManager.SubscribeMouseMove(MouseHandler)
    hookManager.SubscribeMouseAllButtons(MouseButtons)
    hookManager.SubscribeMouseWheel(MouseWheel)
    hookManager.SubscribeKeyDown(KeyboardHandlerDown)
    hookManager.SubscribeKeyUp(KeyboardHandlerUp)
    hookManager.HookMouse()
    hookManager.HookKeyboard()
    while True:
        pythoncom.PumpWaitingMessages()


pid = win32api.GetCurrentProcessId()
handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)

init()

if __name__ == '__main__':
    num_processes = 4
    eventQueue = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=hookThread, args=(eventQueue,))
    p1.start()
    p2 = multiprocessing.Process(target=queueThread, args=(eventQueue,))
    p2.start()
    p2.join()

