import cv2
import numpy as np

cap = cv2.VideoCapture(0)

ret, frame = cap.read()
if not ret:
    cap.release()
    exit()

trace_canvas = np.zeros_like(frame)

# --- 색상 설정 ---
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255)]
color_index = 0
current_color = colors[color_index]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1, upper_red1 = np.array([0, 120, 70]), np.array([10, 255, 255])
    lower_red2, upper_red2 = np.array([170, 120, 70]), np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)

    M = cv2.moments(mask)
    if M['m00'] > 500:
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])

        # 현재 설정된 색상(current_color)으로 점 그리기
        cv2.circle(trace_canvas, (cx, cy), 5, current_color, -1)

    result = cv2.addWeighted(frame, 1, trace_canvas, 1, 0)

    cv2.circle(result, (30, 30), 10, current_color, -1)
    cv2.putText(result, "Color Mode (P to change)", (50, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow('Tracking Red Object', result)

    # 키 입력 처리
    key = cv2.waitKey(1) & 0xFF

    if key == ord('p') or key == ord('P'):
        color_index = (color_index + 1) % len(colors)
        current_color = colors[color_index]

    elif key == ord('c') or key == ord('C'):
        trace_canvas = np.zeros_like(frame)
        print("기록이 삭제되었습니다.")

    elif key == 27:
        break

cap.release()
cv2.destroyAllWindows()