
import cv2
import sys

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_RBUTTONDBLCLK:
        print("왼쪽 버튼 클릭:", x, y)


# 이미지 불러오기
img = cv2.imread("C:/Users/302-25/Downloads/lena.jpg")

if img is None:
    print("이미지를 찾을 수 없습니다.")
    sys.exit()

cv2.imshow('Lena Window', img)  # 윈도우 창 제목, 이미지 객체
cv2.setMouseCallback('Lena Window', mouse_callback)
# 키 입력 대기 (아무 키나 누르면 종료)
cv2.waitKey()
cv2.destroyAllWindows()