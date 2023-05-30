from pathlib import Path
import os
import sys
import cv2
import torch

print("CUDA available: " + str(torch.cuda.is_available()))

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

model = torch.hub.load('ultralytics/yolov5', 'custom', path=ROOT / 'csgo-detection-final.pt')

# Settings of Model
model.classes = 0  # filter only enemies
model.conf = 0.25
model.iou = 0.45

# Check for CUDA
if torch.cuda.is_available():
    model.cuda()


def test():
    screenshot_dir = ROOT / 'images'
    screenshots = list(screenshot_dir.iterdir())
    for image in screenshots:
        results = model(image)
        img = results.render()
        img_box = img[0]
        im_rgb = cv2.cvtColor(img_box, cv2.COLOR_BGR2RGB)
        cv2.imshow("Predicition", im_rgb)
        cv2.waitKey(1)


def detect(img):
    results = model(img)
    boxes = results.pandas().xyxy[0]
    return boxes


