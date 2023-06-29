import cv2

img = cv2.imread('images.jpeg')
cv2.imshow('img',img)
print("Press any key to quit")
cv2.waitKey(0)
