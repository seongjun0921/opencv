1. `512x512` 크기의 흰색 빈 캔버스 생성
2. 마우스 왼쪽 버튼을 누른 채로 이동(Drag)을 통해  그림 그리기
4. `c`를 누르면 캔버스 초기화
5. `q` 또는 `ESC`를 누르면 프로그램이 종료

if flags & cv2.EVENT_FLAG_LBUTTON:
마우스 왼쪽버튼이 눌려져있는지 확인

while True:
    key = cv2.waitKey(0)
    if key == ord('c'):
        canvas.fill(255)
        cv2.imshow('canvas', canvas)
    elif key == ord('q') or key == 27:
        break
    else:
        cv2.imshow('canvas', canvas)

key 입력 받은뒤 while 문 처리
key 따로 입력받지 않으면 waitKey마다 입력 받음

