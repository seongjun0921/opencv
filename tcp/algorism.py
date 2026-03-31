import socket
import json
import time
import math


def normalize_angle(angle):
    """각도를 -pi ~ pi 범위로 정규화"""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


class SmartRobot:
    def __init__(self, name, server_ip):
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (server_ip, 9999)
        self.state = None

        self.prev_x = None
        self.prev_y = None
        self.total_distance = 0.0

        # 센서 인덱스별 로봇 기준 상대 각도 (0: 정면, 1: 45도 좌측...)
        self.sensor_angles = [0, math.pi / 4, math.pi / 2, 3 * math.pi / 4, math.pi, -3 * math.pi / 4, -math.pi / 2,
                              -math.pi / 4]

    def connect(self):
        try:
            self.sock.connect(self.server_address)
            msg = json.dumps({"action": "set_name", "name": self.name})
            self.sock.sendall((msg + "\n").encode())
            return True
        except Exception as e:
            print("[ERROR] 연결 실패:", e)
            return False

    def send_drive(self, l_speed, r_speed):
        try:
            msg = json.dumps({"action": "drive", "l_dist": l_speed, "r_dist": r_speed})
            self.sock.sendall((msg + "\n").encode())
            response = self.sock.recv(2048).decode().strip()
            if response:
                self.state = json.loads(response.split('\n')[-1])
                return True
        except:
            return False
        return False

    def run(self):
        if not self.connect(): return
        self.send_drive(0, 0)

        stuck_count = 0  # 끼임 감지 카운터

        while self.state:
            if self.state.get('result') == 'finished':
                print(f"도착! 총 거리: {self.total_distance:.2f}")
                break

            x, y = self.state['current_pos_x'], self.state['current_pos_y']
            theta = self.state['current_theta']
            goal_x, goal_y = self.state['goal_x'], self.state['goal_y']
            sensors = self.state['sensor']

            # [끼임 감지] 이동 거리 계산
            if self.prev_x is not None:
                dist_moved = math.hypot(x - self.prev_x, y - self.prev_y)
                self.total_distance += dist_moved
                # 속도가 너무 느리면 카운트 증가
                if dist_moved < 0.01:
                    stuck_count += 1
                else:
                    stuck_count = max(0, stuck_count - 1)
            self.prev_x, self.prev_y = x, y

            # ---------------------------------------------------------
            # 점수 기반 의사결정
            # ---------------------------------------------------------
            target_theta = math.atan2(goal_y - y, goal_x - x)
            best_score = -float('inf')
            best_angle_error = 0

            # 끼임 상태 판단 (예: 20스텝 동안 거의 못 움직임)
            is_stuck = stuck_count > 20

            for i in range(8):
                candidate_theta = theta + self.sensor_angles[i]

                # 1. 목적지 점수 (끼었을 때는 목적지보다 탈출 우선)
                angle_diff = abs(normalize_angle(candidate_theta - target_theta))
                goal_score = (math.pi - angle_diff) / math.pi * 100
                if is_stuck: goal_score *= 0.2  # 끼었을 땐 목적지 점수 비중 축소

                # 2. 장애물 점수 (거리가 15 미만이면 급격한 페널티)
                dist = sensors[i]
                if dist < 12:
                    obstacle_score = -200  # 너무 가까우면 아예 제외 수준
                else:
                    obstacle_score = (min(dist, 40) / 40) * 120

                total_score = goal_score + obstacle_score

                if total_score > best_score:
                    best_score = total_score
                    best_angle_error = normalize_angle(candidate_theta - theta)

            # ---------------------------------------------------------
            # 제어 명령 생성
            # ---------------------------------------------------------
            if is_stuck:
                print("[EMERGENCY] 끼임 감지! 탈출 모드 작동")
                base_speed = 2.0  # 천천히 탈출
                turn_gain = 10.0  # 강하게 회전
            else:
                base_speed = 10.0
                turn_gain = 6.0

            l_speed = base_speed - (turn_gain * best_angle_error)
            r_speed = base_speed + (turn_gain * best_angle_error)

            # 후진이 필요할 때 (모든 앞방향 점수가 낮을 때)
            if best_score < -50:
                l_speed, r_speed = -3, -3  # 일단 뒤로 빼기

            l_speed = max(min(l_speed, 10.0), -10.0)
            r_speed = max(min(r_speed, 10.0), -10.0)

            if not self.send_drive(l_speed, r_speed): break
            time.sleep(0.05)

        self.sock.close()


if __name__ == "__main__":
    SmartRobot("ScoreBaseBot", "192.168.0.187").run()