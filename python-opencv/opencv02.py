import cv2

src1 = cv2.imread("C:/Users/302-25/Downloads/dog.jpg")
src1 = cv2.resize(src1, (512, 512))
lena = cv2.imread("C:/Users/302-25/Downloads/lena.jpg")

green_mask = cv2.inRange(src1, (0, 120, 0), (100, 255, 100))
mask_inv = cv2.bitwise_not(green_mask)
dst = cv2.bitwise_and(src1, src1, mask=mask_inv)

cv2.imshow("green", green_mask)
cv2.imshow("mask", mask_inv)
cv2.imshow("dst", dst)
cv2.waitKey(0)
cv2.destroyAllWindows()
