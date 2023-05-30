import csv
import shutil
from pathlib import Path
import os

pathStr = os.path.dirname(os.path.dirname(__file__))
path = Path(pathStr + '/pre-study-data-with-Arduino')
dst_screenshots = Path('./screenshots')
dst_screenshots.mkdir(parents=True, exist_ok=True)
subdir = [x for x in path.iterdir() if x.is_dir()]
big_csv = open('mouse.csv', 'w', newline='')
csv_writer = csv.writer(big_csv, delimiter=';', )
csv_writer.writerow(["ID", "timeStamp", "mousePosX", "mousePosY", "mouseLeftButton", "mouseMiddleButton",
                     "mouseRightButton", "currentKeys"])
j = -1
i = 0
for curr_dir in subdir:
    csvFile = curr_dir / '0' / 'preStudyData.csv'
    if csvFile.exists():
        print(f'Started Copying files from {curr_dir}')
        if i > 0:
            csv_writer.writerow(['NaN', 'NaN', 'NaN', 'NaN', 'NaN', 'NaN', 'NaN', 'NaN'])
        screenshot_dir = curr_dir / '0' / 'screenshots'
        screenshots = list(screenshot_dir.iterdir())
        for image in screenshots:
            time = image.name.split('_')
            shutil.copy(image, dst_screenshots / f'{j+1}_{i}_{time[0]}_screenshot.jpg')
            i += 1
        csv_file = open(csvFile, newline='')
        mouse = csv.reader(csv_file, delimiter=';')
        for row in mouse:
            if row[0] != 'ID':
                myId = row[0]
                if myId == '1':
                    j += 1
                csv_writer.writerow(
                    [str(f"{j}_{myId}"), row[1].replace(',', '.'), row[2], row[3], row[4], row[5], row[6], row[7]])