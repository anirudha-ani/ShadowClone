# Reproducing issue https://github.com/aiortc/aiortc/issues/731
# If you import aiortc and cv2 at the same time, cv2.imshow does not work

import numpy as np
import cv2
import aiortc # if you comment this line, the program will work fine

img = 255 * np.ones((512, 1920 // 2, 3), dtype=np.uint8)
for i in range(1000):
    cv2.imshow("win", img)
    print(i)
    cv2.waitKey(1)