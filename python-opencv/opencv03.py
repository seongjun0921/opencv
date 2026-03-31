import cv2
import numpy as np

src = cv2.imread("C:/Users/302-25/Downloads/lena.jpg")

sharp_mask = np.array(([-1, -1, -1],
                       [-1, 9, -1],
                       [-1, -1, -1],))
dst_sharp = cv2.filter2D(src, -1, sharp_mask)

cv2.imshow("dst", dst_sharp)
cv2.waitKey(0)
cv2.destroyAllWindows()     