import cv2
import numpy as np

img = cv2.imread("coins.jpg")
gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
dst = cv2.equalizeHist(gray_img)

_, thresh =  cv2.threshold(dst, 105, 200, cv2.THRESH_BINARY_INV)

dilate_img = cv2.dilate(thresh, None, iterations=4)
erode_img = cv2.erode(dilate_img, None, iterations=3)

contours, _ = cv2.findContours(erode_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
result = cv2.drawContours(img, contours, -1, (0, 255, 0), 3)
# cv2.putText(img, contours, (50, 50),  (0, 0, 0), 5)

cv2.imshow("threshold", thresh)
cv2.imshow("dilation", dilate_img)
cv2.imshow("erode", erode_img)
cv2.imshow("result", result)
cv2.waitKey(0)
cv2.destroyAllWindows()