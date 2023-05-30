import random
import json


delayCount = 60*60
lastDelayRange = 15


def createDelay(min,max):
    random_delay = []
    lastRandom = min
    for i in range(delayCount):
        if lastRandom <= (min+lastDelayRange):
            lastRandom = random.randint(min / 5, (lastRandom+lastDelayRange) / 5) * 5
        elif lastRandom >= (max-lastDelayRange):
            lastRandom = random.randint((lastRandom-lastDelayRange) / 5, max / 5) * 5
        else:
            lastRandom = random.randint((lastRandom-lastDelayRange) / 5, (lastRandom+lastDelayRange) / 5) * 5
        random_delay.append(lastRandom)
    return random_delay


def init():
    with open("delay100.txt", "w") as f:
        data = createDelay(50,100)
        json.dump(data,f)
    with open("delay150.txt", "w") as f:
        data = createDelay(100,150)
        json.dump(data,f)


init()
