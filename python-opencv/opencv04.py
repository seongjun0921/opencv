import cv2

img = cv2.imread(r"C:\Users\302-25\Downloads\lena.jpg")
rows, cols, channels = img.shape
arr1 = cv2.getRotationMatrix2D((rows/2, cols/2), 45, 0.5)
arr2 = cv2.getRotationMatrix2D((rows/2, cols/2), -45, 1.2)

dst1 = cv2.warpAffine(img, arr1, (cols, rows))
dst2 = cv2.warpAffine(img, arr2, (cols, rows))
cv2.imshow("dst1", dst1)
cv2.imshow("dst2", dst2)
cv2.waitKey(0)
cv2.waitKey(0)
cv2.destroyAllWindows()
