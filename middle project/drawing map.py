import tkinter as tk
from tkinter import ttk
import math
import time
import requests
import numpy as np
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pymysql
from queue import Queue, Empty


# MySQL 접속 정보
MYSQL_HOST = "192.168.0.187"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "0000"
MYSQL_DB = "group4"
MYSQL_TABLE = "system_logs"


# ================= 설정 =================
URL = "http://192.168.0.243:6420/control"
INTERVAL = 50  # UI 갱신 주기를 0.05초로 단축


# --- 초기 제어 파라미터 ---
DEFAULT_LIN = 0.12
DEFAULT_ANG = 0.6
WP_TOL = 0.20
HOME_TOL_DIST = 0.005
HOME_TOL_ANG = 0.0025
DIST_NEAR_WP = 0.40
SPEED_MIN = 0.04
PARKING_PRECISION = 0.005
ANGLE_TOL = 0.005


# --- 안전 및 라이다 설정 ---
FRONT_STOP_DIST = 0.15
LIDAR_SAMPLE_STEP = 2
LIDAR_HISTORY = 1000
LIDAR_NEAR_DIST = 5.0
DENSITY_THRESHOLD = 0.04




class AbsoluteMapZoomController(tk.Tk):
   def __init__(self):
       super().__init__()
       self.title("거북이 관제 시스템 - 고속 통신 모드")
       self.geometry("1200x950")


       self._last_evade_log_time = 0.0
       self._last_evade_point = None


       # --- 통신 최적화 설정 ---
       self.session = requests.Session()
       self.current_telemetry = None  # 최신 데이터를 담을 버퍼


       self.roi_pos = None
       self.roi_marker = None
       self.roi_text = None


       self.line_mode = False  # 라인 그리기 ON/OFF
       self.line_points = []  # raw 드래그 좌표
       self.line_plot = None  # matplotlib line 객체
       self.is_drawing_line = False


       self.last_click_time = 0
       self.double_click_delay = 0.20


       self.is_running = False
       self.waypoints = []
       self.wp_markers = []
       self.wp_texts = []
       self.wp_lines = []
       self.draw_counter = 0
       self.home_pos = None
       self.home_angle = 0.0
       self.home_init_samples = []


       self.cmd_lin = 0.0
       self.cmd_ang = 0.0


       self.obstacle_points_x = []
       self.obstacle_points_y = []
       self.point_weights = []


       self.path_history_x = []
       self.path_history_y = []


       self.zoom_scale = 1.1
       self.offset_x = 0.0
       self.offset_y = 0.0
       self.rx, self.ry, self.ra = 0.0, 0.0, 0.0
       self.latest_lidar = []


       self.log_queue = Queue()
       self.db_worker_running = False
       self.db_conn = None
       self.db_cur = None


       # 드래그 상태 관리를 위한 변수
       self.is_dragging = False
       self.press_x = None
       self.press_y = None


       # 기존 바인딩 아래에 추가


       self._create_layout()
       self._create_menubar()


       self.canvas.mpl_connect('button_press_event', self.on_press)
       self.canvas.mpl_connect('button_release_event', self.on_release)
       self.canvas.mpl_connect('motion_notify_event', self.on_motion)


       # DB 초기화 및 저장 전용 스레드 시작
       self._init_log_db_mysql()
       self._start_log_db_worker_mysql()


       # 창 닫을 때 DB 안전 종료를 위한 바인딩
       self.protocol("WM_DELETE_WINDOW", self.on_close)


       # 이벤트 바인딩
       self.canvas.mpl_connect('button_press_event', self.on_map_click)
       self.canvas.mpl_connect('scroll_event', self.on_scroll)




       # 1. 데이터 수신 전용 스레드 시작
       threading.Thread(target=self.fetch_data_worker, daemon=True).start()


       # 2. UI 업데이트 루프 시작
       self.after(INTERVAL, self.update_status)


   def reverse_by_distance(self, target_dist=0.10, speed=0.08):
       """
       정확히 target_dist(m) 만큼 후진
       """
       start_x, start_y = self.rx, self.ry


       self.log(f"↩️ 거리 기반 후진 시작 ({target_dist:.2f}m)")


       while self.is_running:
           moved = math.hypot(self.rx - start_x, self.ry - start_y)
           if moved >= target_dist:
               break


           self.send_command(-speed, 0.0)
           time.sleep(0.04)


       self.send_command(0, 0)
       self.log("✅ 거리 기반 후진 완료")


   def toggle_line_mode(self):
       self.line_mode = not self.line_mode
       state = "ON" if self.line_mode else "OFF"
       self.log(f"✏️ 라인 그리기 모드 {state}")


   def on_press(self, event):
       if event.inaxes != self.ax: return


       # 📌 라인 그리기 시작
       if self.line_mode and event.button == 1:
           self.is_drawing_line = True
           self.line_points = [(event.xdata, event.ydata)]


           if self.line_plot:
               self.line_plot.remove()


           self.line_plot, = self.ax.plot(
               [event.xdata], [event.ydata],
               color="orange", linewidth=2
           )
           self.canvas.draw_idle()
           return


       # 기존 맵 이동
       if event.button == 2:
           self.is_dragging = True
           self.press_x = event.xdata
           self.press_y = event.ydata


   def on_motion(self, event):
       if event.inaxes != self.ax: return


       # ✏️ 라인 드래그 중
       if self.is_drawing_line and self.line_mode:
           self.line_points.append((event.xdata, event.ydata))
           xs, ys = zip(*self.line_points)
           self.line_plot.set_data(xs, ys)
           self.canvas.draw_idle()
           return


       # 기존 맵 이동
       if self.is_dragging:
           dx = event.xdata - self.press_x
           dy = event.ydata - self.press_y
           cur_xlim = self.ax.get_xlim()
           cur_ylim = self.ax.get_ylim()
           self.ax.set_xlim(cur_xlim[0] - dx, cur_xlim[1] - dx)
           self.ax.set_ylim(cur_ylim[0] - dy, cur_ylim[1] - dy)
           self.canvas.draw_idle()


   def on_release(self, event):
       if event.button == 1 and self.is_drawing_line:
           self.is_drawing_line = False
           self.log(f"✏️ 라인 입력 완료 ({len(self.line_points)} points)")
           return


       if event.button == 2:
           self.is_dragging = False
       elif event.button == 1 and event.inaxes == self.ax:
           # 클릭 시점과 뗀 시점의 거리가 짧을 때만 WP 생성 (0.1m 기준)
           if self.press_x is not None:
               dist = math.hypot(event.xdata - self.press_x, event.ydata - self.press_y)
               if dist < 0.1:
                   self.on_map_click(event)

           # 좌표 초기화
       self.press_x = self.press_y = None

   def clear_line(self):
       self.line_points.clear()
       if self.line_plot:
           self.line_plot.remove()
           self.line_plot = None
       self.canvas.draw_idle()
       self.log("🧹 라인 초기화 완료")


   def smooth_line(self, points, step=0.15):
       if len(points) < 3:
           return points


       smoothed = [points[0]]
       acc = 0.0


       for i in range(1, len(points)):
           x0, y0 = points[i - 1]
           x1, y1 = points[i]
           d = math.hypot(x1 - x0, y1 - y0)
           acc += d


           if acc >= step:
               smoothed.append((x1, y1))
               acc = 0.0


       smoothed.append(points[-1])
       return smoothed


   def start_line_navigation(self):
       if len(self.line_points) < 3:
           self.log("⚠️ 라인이 너무 짧습니다.")
           return


       smooth_path = self.smooth_line(self.line_points)


       self.is_running = True
       threading.Thread(
           target=self.navigation_thread,
           args=(smooth_path, "라인 주행"),
           daemon=True
       ).start()


       self.log("🚗 라인 따라 주행 시작")


   def get_evasion_point(self, obs_dist, is_reverse=False):
       """
       장애물을 발견했을 때, 진행 방향에 맞춰 회피 지점을 생성합니다.
       """
       if self.latest_lidar is None or len(self.latest_lidar) == 0:
           return None


       n = len(self.latest_lidar)


       # 1. 진행 방향(전진/후진)에 따른 좌우 시야 설정
       if not is_reverse:
           # 전진 시: 앞쪽 좌측과 우측 확인
           left_view = self.latest_lidar[n // 12: n // 4]
           right_view = self.latest_lidar[3 * n // 4: 11 * n // 12]
           base_angle = self.ra
       else:
           # 후진 시: 뒤쪽 좌측과 우측 확인 (시야를 뒤로 반전)
           left_view = self.latest_lidar[7 * n // 12: 3 * n // 4]
           right_view = self.latest_lidar[n // 4: 5 * n // 12]
           base_angle = self.ra + math.pi


       l_min = np.min(left_view[left_view > 0.05]) if len(left_view[left_view > 0.05]) > 0 else 5.0
       r_min = np.min(right_view[right_view > 0.05]) if len(right_view[right_view > 0.05]) > 0 else 5.0


       # 2. 회피 방향 결정 (과감하게 꺾기 위해 1.4 라디안 사용)
       evade_direction = 0.60 if l_min > r_min else -0.60
       target_angle = base_angle + evade_direction


       # 3. 회피 지점 좌표 계산 (거리를 0.7m로 늘려 확실히 우회)
       evade_x = self.rx + 0.40 * math.cos(target_angle)
       evade_y = self.ry + 0.40 * math.sin(target_angle)
       new_pt = (evade_x, evade_y)


       # ===== [핵심 수정] 로그 폭주 방지 =====
       now = time.time()


       moved_enough = (
               self._last_evade_point is None or
               math.hypot(new_pt[0] - self._last_evade_point[0], new_pt[1] - self._last_evade_point[1]) > 0.04
       )
       cooldown_ok = (now - self._last_evade_log_time) > 0.8


       if moved_enough and cooldown_ok:
           self.log(f"📍 회피 좌표 설정: ({evade_x:.2f}, {evade_y:.2f})")
           self._last_evade_log_time = now
           self._last_evade_point = new_pt


       return new_pt


   def get_dynamic_evasion_angle(self, evade_wp):
       """우회 지점으로 이동하면서 측면 장애물과의 거리를 실시간 반영하여 각도를 조절합니다."""
       if self.latest_lidar is None: return 0.0


       # 1. 기본 목표(우회 WP)를 향한 각도 (Pure Pursuit 방식)
       tx, ty = evade_wp
       target_a = math.atan2(ty - self.ry, tx - self.rx)
       base_diff_a = (target_a - self.ra + math.pi) % (2 * math.pi) - math.pi


       # 2. 측면 장애물 간격 유지 (측면 척력 추가)
       n = len(self.latest_lidar)
       side_repulsion = 0.0


       # 로봇의 측면(좌우 60~120도) 라이다 데이터 확인
       left_side = self.latest_lidar[n // 6: n // 3]
       right_side = self.latest_lidar[2 * n // 3: 5 * n // 6]


       l_dist = np.min(left_side[left_side > 0.05]) if len(left_side[left_side > 0.05]) > 0 else 2.0
       r_dist = np.min(right_side[right_side > 0.05]) if len(right_side[right_side > 0.05]) > 0 else 2.0


       # 안전 마진 (0.45m). 이보다 가까워지면 반대 방향으로 밀어내는 힘 부여
       safe_margin = 0.45
       if l_dist < safe_margin:
           side_repulsion -= (safe_margin - l_dist) * 2.0  # 오른쪽으로 회전 유도
       if r_dist < safe_margin:
           side_repulsion += (safe_margin - r_dist) * 2.0  # 왼쪽으로 회전 유도


       return base_diff_a + side_repulsion


   def get_avoidance_angle(self):
       """
       라이다 전체 데이터를 활용하여 장애물이 밀어내는 힘(척력)의 합산 방향을 계산합니다.
       [개선] 고정값 1.0이 아닌 계산된 각도를 반환하여 부드러운 조향을 유도합니다.
       """
       if self.latest_lidar is None or len(self.latest_lidar) == 0:
           return 0.0


       n = len(self.latest_lidar)
       repulsion_x = 0.0
       repulsion_y = 0.0
       sensor_angles = np.linspace(0, 2 * np.pi, n, endpoint=False)


       for i in range(n):
           dist = self.latest_lidar[i]
           angle = sensor_angles[i]


           # 0.60m 이내의 장애물에 대해 척력 계산
           if 0.05 < dist < 0.55:
               # 척력 가중치 (거리에 반비례)
               weight = (1.0 / dist) ** 2
               repulsion_x -= weight * math.cos(angle)
               repulsion_y -= weight * math.sin(angle)


       if abs(repulsion_x) < 0.1 and abs(repulsion_y) < 0.1:
           return 0.0


       # 장애물들이 밀어내는 종합적인 각도 계산
       avoid_direction = math.atan2(repulsion_y, repulsion_x)


       # [핵심 수정] 강제 1.0/-1.0 대신, 계산된 각도만큼 부드럽게 꺾음 (최대 1.2로 제한)
       # 이렇게 해야 로봇이 장애물 위치에 따라 미세하게 혹은 과감하게 조절합니다.
       return np.clip(avoid_direction, -1.0, 1.0)


   def fetch_data_worker(self):
       """백그라운드에서 로봇 데이터를 지속적으로 수집 (Blocking 방지)"""
       while True:
           try:
               # HTTP 연결 재사용을 통해 속도 향상
               res = self.session.get(URL, timeout=0.1).json()
               self.current_telemetry = res
           except Exception:
               pass
           time.sleep(0.04)  # 약 25Hz로 데이터 수집


   def send_command(self, lin, ang):
       """비동기 방식으로 로봇에게 명령 전송"""


       def _send():
           try:
               self.session.get(f"{URL}?lin={lin:.2f}&ang={ang:.2f}", timeout=0.05)
           except:
               pass


       threading.Thread(target=_send, daemon=True).start()


   def update_status(self):
       """수신된 데이터를 UI에 반영 (통신 코드를 포함하지 않음)"""
       # 아이콘 위치 갱신
       self.robot_icon.set_position((self.rx, self.ry))


       # 아이콘 회전 갱신 (라디안 → 도)
       heading_deg = math.degrees(self.ra)


       # "▲"는 기본이 위(+Y)를 향하니까,
       # 로봇 ra가 +X(오른쪽)를 0도로 쓰는 좌표계라면 -90 보정이 자연스러움.
       self.robot_icon.set_rotation(heading_deg - 90)
       if self.current_telemetry:
           try:
               data = self.current_telemetry
               odom = data["p"]
               self.rx, self.ry, self.ra = odom['x'] + self.offset_x, odom['y'] + self.offset_y, odom['a']
               self.latest_lidar = np.array(data["s"], dtype=float) / 100.0
               num_points = len(self.latest_lidar)
               angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)




               if not self.path_history_x or math.hypot(self.rx - self.path_history_x[-1],
                                                        self.ry - self.path_history_y[-1]) > 0.05:
                   self.path_history_x.append(self.rx)
                   self.path_history_y.append(self.ry)
                   self.path_plot.set_data(self.path_history_x, self.path_history_y)




               if self.home_pos is None:
                   self.home_init_samples.append((self.rx, self.ry, self.ra))
                   if len(self.home_init_samples) >= 10:
                       arr = np.array(self.home_init_samples)
                       self.home_pos = (np.mean(arr[:, 0]), np.mean(arr[:, 1]))
                       self.home_angle = np.mean(arr[:, 2])
                       self.log(f"🏠 Home 초기화 완료")




               # UI 갱신
               self.pos_label.config(text=f"X: {self.rx:.2f} Y: {self.ry:.2f}")
               self.speed_monitor_label.config(text=f"Lin: {self.cmd_lin:.2f} / Ang: {self.cmd_ang:.2f}")


               self.robot_icon.set_position((self.rx, self.ry))
               ARROW_LEN = 0.25  # ← 여기 줄이면 더 짧아짐

               start = (self.rx, self.ry)
               end = (
                   self.rx + ARROW_LEN * math.cos(self.ra),
                   self.ry + ARROW_LEN * math.sin(self.ra)
               )

               self.robot_dir.set_positions(start, end)

               mask = self.latest_lidar > 0.05
               if hasattr(self, 'lidar_plot'):  # lidar_plot 객체가 있는 경우만
                   self.lidar_plot.set_data(angles[mask], self.latest_lidar[mask])
                   self.canvas_lidar.draw_idle()


               sampled_indices = np.arange(0, num_points, LIDAR_SAMPLE_STEP)
               valid_mask = self.latest_lidar[sampled_indices] > 0.05


               current_distances = self.latest_lidar[sampled_indices][valid_mask]
               current_angles = angles[sampled_indices][valid_mask]


               # 절대 좌표 변환 (로봇 위치 + 현재 라이다 측정값)
               wx = self.rx + current_distances * np.cos(current_angles + self.ra)
               wy = self.ry + current_distances * np.sin(current_angles + self.ra)


               for x, y in zip(wx, wy):
                   dist_to_robot = math.hypot(x - self.rx, y - self.ry)
                   if dist_to_robot < LIDAR_NEAR_DIST:
                       # (기존 장애물 필터링 로직 유지)
                       self.obstacle_points_x.append(x)
                       self.obstacle_points_y.append(y)
                       self.point_weights.append(1)


               if len(self.obstacle_points_x) > LIDAR_HISTORY:
                   self.obstacle_points_x = self.obstacle_points_x[-LIDAR_HISTORY:]
                   self.obstacle_points_y = self.obstacle_points_y[-LIDAR_HISTORY:]


               self.scat.set_offsets(np.c_[self.obstacle_points_x, self.obstacle_points_y])
               self.canvas.draw_idle()
           except Exception as e:
               pass


       self.after(INTERVAL, self.update_status)


   def start_exploration(self):
       if self.explore_target: self.is_running = True;
       threading.Thread(target=self.exploration_thread, daemon=True).start()


   def navigation_thread(self, target_list, mission_name="주행", is_reverse=False):
       self.log(f"▶ {mission_name} 시작 (정밀 모드)")
       # ===== [주차 미션 공통 초기 시퀀스] =====
       if mission_name in ["전진 주차", "후진 주차"]:
           # 1. 무조건 10cm 후진
           self.reverse_by_distance(target_dist=0.10)


           # 2. 주차 목적지(Home)를 향한 각도 정렬
           tx, ty = target_list[0]
           target_angle = math.atan2(ty - self.ry, tx - self.rx)
           self.align_angle(target_angle)


           self.log("🅿️ 주차 초기 정렬 완료 → 주차 이동 시작")


       idx = 0
       evade_wp = None
       total_wps = len(target_list)
       parking_mode_triggered = False


       PARKING_DIST_TOL = 0.005  # 주차 위치 인정


       is_line_mission = (mission_name == "라인 주행")


       while self.is_running and idx < len(target_list):
           try:
               tx, ty = target_list[idx]
               dist_to_wp = math.hypot(tx - self.rx, ty - self.ry)


               # 1. 미션별 tolerance
               is_parking_mission = "주차" in mission_name or "복귀" in mission_name
               current_tol = PARKING_DIST_TOL if is_parking_mission else WP_TOL


               # 2. 후진 주차 로직
               current_reverse = is_reverse
               if mission_name == "후진 주차":
                   if not parking_mode_triggered:
                       if dist_to_wp > 0.40:
                           current_reverse = False
                       else:
                           self.log("🔄 후진 주차 정렬")
                           self.send_command(0, 0)
                           time.sleep(0.5)
                           angle_to_wp = math.atan2(self.ry - ty, self.rx - tx)
                           self.align_angle(angle_to_wp)
                           parking_mode_triggered = True
                           current_reverse = True
                   else:
                       current_reverse = True


               # 3. 장애물 감지
               obs_dist = self.check_front_obstacle(current_reverse)


               if parking_mode_triggered or dist_to_wp < DIST_NEAR_WP:
                   evade_wp = None
               else:
                   if evade_wp and obs_dist < 0.45:
                       evade_wp = None
                   if obs_dist < 0.45 and evade_wp is None:
                       evade_wp = self.get_evasion_point(obs_dist, current_reverse)
                   if evade_wp and math.hypot(evade_wp[0] - self.rx, evade_wp[1] - self.ry) < 0.15:
                       evade_wp = None


               # 4. 조향 각 계산
               if evade_wp:
                   diff_a = self.get_dynamic_evasion_angle(evade_wp)
               else:
                   if not current_reverse:
                       target_a = math.atan2(ty - self.ry, tx - self.rx)
                   else:
                       target_a = math.atan2(self.ry - ty, self.rx - tx)
                   diff_a = (target_a - self.ra + math.pi) % (2 * math.pi) - math.pi


               # 5. 도착 판정
               if dist_to_wp < current_tol:
                   self.log(f"📍 목적지 도착 (오차: {dist_to_wp:.3f}m)")


                   # ROI 도착 시
                   if mission_name == "ROI 구역 탐색":
                       self.send_command(0, 0)
                       time.sleep(0.5)
                       self.follow_wall_sequence(target_dist=0.05, duration=20.0)


                   # 주차 미션
                   if is_parking_mission:
                       self.send_command(0, 0)
                       time.sleep(0.5)
                       self.align_angle(self.home_angle)
                       self.log(f"🅿️ {mission_name} 완료")
                       break


                   # 🔥 [추가] WP → WP 전환 시 거리 기반 10cm 후진
                   # 🔥 WP → WP 전환 시: 거리 기반 후진 + 다음 WP 각도 정렬
                   if (
                           mission_name == "웨이포인트 주행"
                           and idx < len(target_list) - 1
                   ):
                       # 1. 10cm 거리 기반 후진
                       self.reverse_by_distance(target_dist=0.10)


                       # 2. 다음 WP 기준 각도 정렬
                       next_wp = target_list[idx + 1]
                       nx, ny = next_wp
                       target_angle = math.atan2(ny - self.ry, nx - self.rx)


                       self.align_angle(target_angle)


                   idx += 1
                   continue


               # 6. 구동 명령
               max_lin = self.lin_speed_var.get()
               max_ang = self.ang_speed_var.get()


               if obs_dist < 0.12:
                   self.send_command(0, 0)
               else:
                   if mission_name == "라인 주행":
                       speed_factor = 1.0
                   else:
                       speed_factor = 0.5 if (evade_wp or dist_to_wp < DIST_NEAR_WP) else 1.0


                   # 🔥 라인 주행 전용: 각도 기반 속도 분배
                   if is_line_mission:
                       angle_mag = abs(diff_a)


                       lin_scale = max(0.25, 1.0 - angle_mag / 1.0)
                       lin = max_lin * lin_scale * speed_factor
                       if current_reverse:
                           lin = -lin


                       ang = np.clip(diff_a * 1.2, -max_ang, max_ang)


                       # 급커브 시 제자리 회전
                       if angle_mag > 1.2:
                           lin = 0.0


                   # 🔁 기존 WP / ROI / 주차 주행 (변경 없음)
                   else:
                       lin = -max_lin * speed_factor if current_reverse else max_lin * speed_factor
                       ang = np.clip(0.8 * diff_a, -max_ang, max_ang)


                   self.send_command(lin, ang)


           except Exception as e:
               self.log(f"⚠️ 내비게이션 에러: {e}")


           time.sleep(0.05)


       self.send_command(0, 0)
       self.is_running = False


   def exploration_thread(self):
       cx, cy = self.explore_target
       area_size, step_size = 0.5, 0.15
       path_list = []
       start_x, start_y = cx - area_size / 2, cy - area_size / 2
       y_steps = int(area_size / step_size) + 1


       for i in range(y_steps):
           curr_y = start_y + (i * step_size)
           if i % 2 == 0:
               path_list.extend([(start_x, curr_y), (start_x + area_size, curr_y)])
           else:
               path_list.extend([(start_x + area_size, curr_y), (start_x, curr_y)])
       path_list.append((cx, cy))


       self.log(f"🐍 정밀 탐색 시작")
       idx = 0
       while self.is_running and idx < len(path_list):
           tx, ty = path_list[idx]
           dist = math.hypot(tx - self.rx, ty - self.ry)
           if dist < (0.03 if idx == len(path_list) - 1 else 0.10):
               idx += 1
               continue
           if self.check_front_obstacle() < 0.12:
               idx += 1;
               time.sleep(0.5);
               continue


           target_a = math.atan2(ty - self.ry, tx - self.rx)
           diff_a = (target_a - self.ra + math.pi) % (2 * math.pi) - math.pi
           cmd_lin = (self.lin_speed_var.get() * 0.9) * max(0.1, 1.0 - abs(diff_a))
           cmd_ang = np.clip(diff_a * 2.2, -self.ang_speed_var.get(), self.ang_speed_var.get())
           requests.get(f"{URL}?lin={cmd_lin:.2f}&ang={cmd_ang:.2f}")
           time.sleep(0.04)
       self.is_running = False
       requests.get(f"{URL}?lin=0&ang=0")
       self.log(f"🏁 탐색 완료")


   def align_angle(self, target_angle):
       """목표 각도로 제자리 회전 정렬 (정밀도 강화)"""
       max_ang = self.ang_speed_var.get()
       self.log(f"📐 정밀 각도 정렬 시작 (목표: {math.degrees(target_angle):.1f}°)")


       while self.is_running:
           # 현재 각도와 목표 각도의 차이 계산 (-pi ~ pi 범위)
           diff_a = (target_angle - self.ra + math.pi) % (2 * math.pi) - math.pi


           # [핵심] ANGLE_TOL(약 1.1도) 이내면 정렬 완료
           if abs(diff_a) < ANGLE_TOL:
               break


           # P 제어: 각도 차이가 클수록 빠르게, 작을수록 느리게 회전
           # 1.5는 게인(Gain)값으로, 너무 느리면 2.0으로 높여보세요.
           ang_speed = np.clip(1.0 * diff_a, -max_ang, max_ang)


           # 모터의 최소 구동 전압(Deadzone) 고려: 너무 느리면 안 움직이므로 최소값 보정
           if abs(ang_speed) < 0.15:
               ang_speed = 0.15 if ang_speed > 0 else -0.15


           self.send_command(0, ang_speed)
           time.sleep(0.05)


       self.send_command(0, 0)
       self.log(f"✅ 각도 정렬 완료 (최종 오차: {math.degrees(diff_a):.2f}°)")


   def _create_menubar(self):
       menubar = tk.Menu(self)


       menu_line = tk.Menu(menubar, tearoff=0)
       menu_line.add_command(label="라인 그리기 ON/OFF", command=self.toggle_line_mode)
       menu_line.add_command(label="라인 따라 주행하기", command=self.start_line_navigation)
       menu_line.add_command(label="라인 초기화", command=self.clear_line)
       menubar.add_cascade(label="라인 주행", menu=menu_line)


       menu_nav = tk.Menu(menubar, tearoff=0)
       menu_nav.add_command(label="웨이포인트 주행 시작", command=self.start_navigation)
       menu_nav.add_command(label="ROI 구역 탐색", command=self.start_roi_navigation)
       menu_nav.add_separator()
       menu_nav.add_command(label="현재 위치를 Home으로 설정", command=self.set_current_as_home)
       menu_nav.add_command(label="맵 리셋(줌)", command=self.reset_zoom)
       menu_nav.add_command(label="장애물 데이터 비우기", command=self.clear_obstacles)
       menu_nav.add_command(label="주행 경로 초기화", command=self.clear_path)
       menubar.add_cascade(label="주행제어", menu=menu_nav)


       menu_park = tk.Menu(menubar, tearoff=0)
       menu_park.add_command(label="전진 주차 (Home 위치)", command=lambda: self.start_parking(is_reverse=False))
       menu_park.add_command(label="후진 주차 (Home 위치)", command=lambda: self.start_parking(is_reverse=True))
       menubar.add_cascade(label="주차", menu=menu_park)


       # menu_explore = tk.Menu(menubar, tearoff=0)
       # menu_explore.add_command(label="설정: 지도 더블클릭", state="disabled")
       # menu_explore.add_separator()
       # menu_explore.add_command(label="경로 탐색 시작", command=self.start_exploration)
       # menubar.add_cascade(label="경로탐색", menu=menu_explore)


       self.config(menu=menubar)


   def _create_layout(self):
       self.main_container = ttk.Frame(self)
       self.main_container.pack(fill=tk.BOTH, expand=True)
       self.main_container.rowconfigure(0, weight=6)
       self.main_container.rowconfigure(1, weight=1)
       self.main_container.columnconfigure(0, weight=1)
       self.center_frame = ttk.Frame(self.main_container)
       self.center_frame.grid(row=0, column=0, sticky="nsew")
       self.center_frame.columnconfigure(0, weight=5)
       self.center_frame.columnconfigure(1, weight=1)
       self.map_frame = ttk.Frame(self.center_frame)
       self.map_frame.grid(row=0, column=0, sticky="nsew")
       self.ctrl_panel = ttk.Frame(self.center_frame, padding=10)
       self.ctrl_panel.grid(row=0, column=1, sticky="nsew")
       ttk.Label(self.ctrl_panel, text="[ 지상 관제 시스템 ]", font=('Arial', 12, 'bold')).pack(pady=10)
       self.status_label = tk.Label(self.ctrl_panel, text="상태: 대기 중", fg="blue", font=('Arial', 10))
       self.status_label.pack(pady=5)
       self.pos_label = tk.Label(self.ctrl_panel, text="X: 0.00 Y: 0.00", font=('Courier', 11))
       self.pos_label.pack(pady=5)
       ttk.Separator(self.ctrl_panel, orient='horizontal').pack(fill=tk.X, pady=10)
       ttk.Label(self.ctrl_panel, text="[ 명령 값 ]").pack()
       self.speed_monitor_label = tk.Label(self.ctrl_panel, text="Lin: 0.00 / Ang: 0.00", font=('Courier', 11),
                                           fg="#e67e22")
       self.speed_monitor_label.pack(pady=5)
       ttk.Separator(self.ctrl_panel, orient='horizontal').pack(fill=tk.X, pady=10)
       ttk.Label(self.ctrl_panel, text="최대 이동 속도 (m/s)").pack()
       self.lin_speed_var = tk.DoubleVar(value=DEFAULT_LIN)
       self.lin_slider = tk.Scale(self.ctrl_panel, from_=0.05, to=0.20, resolution=0.01, orient=tk.HORIZONTAL,
                                  variable=self.lin_speed_var)
       self.lin_slider.pack(fill=tk.X)
       ttk.Label(self.ctrl_panel, text="최대 회전 속도 (rad/s)").pack(pady=(5, 0))
       self.ang_speed_var = tk.DoubleVar(value=DEFAULT_ANG)
       self.ang_slider = tk.Scale(self.ctrl_panel, from_=0.1, to=0.8, resolution=0.05, orient=tk.HORIZONTAL,
                                  variable=self.ang_speed_var)
       self.ang_slider.pack(fill=tk.X)
       ttk.Separator(self.ctrl_panel, orient='horizontal').pack(fill=tk.X, pady=10)


       ttk.Label(self.ctrl_panel, text="[ 실시간 라이다 뷰 ]", font=('Arial', 10, 'bold')).pack(pady=(5, 2))
       self.lidar_viz_frame = tk.Frame(self.ctrl_panel, bg="#2c3e50", height=250)
       self.lidar_viz_frame.pack(fill=tk.X, pady=5)
       self.lidar_viz_frame.pack_propagate(False)


       self.fig_lidar = plt.Figure(figsize=(3, 3), dpi=80, facecolor='#2c3e50')
       self.ax_lidar = self.fig_lidar.add_subplot(111, projection='polar')
       self.ax_lidar.set_facecolor('#34495e')
       self.ax_lidar.tick_params(colors='white', labelsize=7)
       self.ax_lidar.grid(True, color='gray', alpha=0.5)
       self.ax_lidar.set_ylim(0, 3.5)


       self.lidar_plot, = self.ax_lidar.plot([], [], 'ro', markersize=2, alpha=0.7)
       self.canvas_lidar = FigureCanvasTkAgg(self.fig_lidar, master=self.lidar_viz_frame)
       self.canvas_lidar.get_tk_widget().pack(fill=tk.BOTH, expand=True)


       tk.Button(self.ctrl_panel, text="비상 정지", command=self.stop_mission, bg="#dc3545", fg="white",
                 font=('Arial', 12, 'bold'), height=2).pack(fill=tk.X, pady=20)
       self.log_frame = ttk.LabelFrame(self.main_container, text=" System Log ")
       self.log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
       self.log_text = tk.Text(self.log_frame, font=("Consolas", 9), bg="#f8f9fa", height=5)
       self.log_text.pack(fill=tk.BOTH, expand=True)
       self.fig = plt.Figure(figsize=(6, 6))
       self.ax = self.fig.add_subplot(111)
       self.ax.set_aspect('equal')
       self.ax.grid(True, linestyle='--', alpha=0.3)

       from matplotlib.patches import FancyArrowPatch

       self.robot_dir = FancyArrowPatch(
           (0, 0), (0, 0),
           arrowstyle='->',
           color='red',
           linewidth=2,
           mutation_scale=12,
           zorder=11
       )
       self.ax.add_patch(self.robot_dir)

       self.ax.set_xlim(-25, 25)
       self.ax.set_ylim(-25, 25)
       self.path_plot, = self.ax.plot([], [], color='#006400', linewidth=1.5, alpha=0.6, zorder=5)
       self.scat = self.ax.scatter([], [], s=2, c="#3498db", alpha=0.5)
       self.robot_icon = self.ax.text(
           0, 0, "🐢",
           fontsize=14, ha="center", va="center",
           rotation=0, rotation_mode="anchor",
           zorder=10, color="#006400"
       )


       try:
           self.robot_icon.set_fontname("Segoe UI Emoji")  # Windows에서 도움
       except:
           pass

       self.explore_marker, = self.ax.plot([], [], 'bx', markersize=10, markeredgewidth=2, visible=False, zorder=12)
       self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
       self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


   def set_current_as_home(self):
       self.home_pos = (self.rx, self.ry)
       self.home_angle = self.ra
       self.log(f"🏠 [Home 갱신] 위치({self.rx:.2f}, {self.ry:.2f}), 각도({math.degrees(self.ra):.1f}°) 저장")

   def check_front_obstacle(self, is_reverse=False):
       """
       로봇 전방(또는 후진 시 후방)의 장애물 유무를 확인합니다.
       감시 범위를 좌우 35도(총 70도)로 설정함.
       """
       if self.latest_lidar is None or len(self.latest_lidar) == 0:
           return 999.0

       n = len(self.latest_lidar)

       # 360도 중 35도에 해당하는 인덱스 범위 계산 (n * 35 / 360)
       fov_idx = n * 35 // 360

       if not is_reverse:
           # 전진 시: 정면(0도) 기준 좌우 35도
           # 0 ~ 35도 범위 및 325(360-35) ~ 360도 범위
           indices = np.where((np.arange(n) < fov_idx) | (np.arange(n) > n - fov_idx))
       else:
           # 후진 시: 후면(180도) 기준 좌우 35도
           # 180도는 n // 2 지점임
           indices = np.where((np.arange(n) > (n // 2) - fov_idx) & (np.arange(n) < (n // 2) + fov_idx))

       front_values = self.latest_lidar[indices]
       valid_values = front_values[front_values > 0.05]

       # 이전 에러(NoneType) 방지를 위해 항상 float 값을 반환하도록 보장
       return np.min(valid_values) if len(valid_values) > 0 else 999.0


   def clear_path(self):
       self.path_history_x = []
       self.path_history_y = []
       self.path_plot.set_data([], [])
       self.canvas.draw_idle()
       self.log("🧹 지도 경로 데이터 초기화")


   def start_navigation(self):
       if not self.waypoints:
           self.log("⚠️ 설정된 웨이포인트가 없습니다.")
           return
       self.is_running = True
       threading.Thread(target=self.navigation_thread, args=(self.waypoints, "웨이포인트 주행"), daemon=True).start()


   def start_return_home(self):
       if self.home_pos is None: return
       self.is_running = True
       threading.Thread(target=self.navigation_thread, args=([self.home_pos], "시작위치 복귀"), daemon=True).start()


   def start_parking(self, is_reverse=False):
       if self.home_pos is None: return
       self.is_running = True
       name = "후진 주차" if is_reverse else "전진 주차"
       threading.Thread(target=self.navigation_thread, args=([self.home_pos], name, is_reverse), daemon=True).start()


   def follow_wall_sequence(self, target_dist=0.05, duration=20.0):
       self.log(f"🧱 벽 타기 최적화 시작 (목표: {target_dist}m)")
       start_time = time.time()


       # 정면에서 까딱거림을 방지하기 위해 게인 조정
       kp_dist = 1.5  # 너무 높으면 정면에서 요동칩니다 (4.0 -> 2.5)
       kp_align = 0.10  # 차라리 평행을 맞추는 힘을 키웁니다


       max_ang = self.ang_speed_var.get()
       max_lin = self.lin_speed_var.get()


       while self.is_running:
           elapsed_time = time.time() - start_time
           if elapsed_time >= duration: break


           if self.latest_lidar is None or len(self.latest_lidar) == 0:
               time.sleep(0.02);
               continue


           lidar = np.array(self.latest_lidar)
           lidar = np.where(lidar > 0.01, lidar, 3.5)


           # [핵심 추가] 1. 정면 장애물 판단 (정면 좌우 20도)
           front_min = np.min(np.concatenate([lidar[-20:], lidar[:20]]))


           # 정면에 벽이 너무 가까우면 (예: 40cm 이내)
           if front_min < 0.40:
               self.log("⚠️ 정면 벽 감지! 제자리 회전 정렬 중...")
               # 왼쪽과 오른쪽 중 더 트인 곳으로 회전
               l_dist = np.mean(lidar[45:90])
               r_dist = np.mean(lidar[270:315])
               turn_dir = 1.0 if l_dist > r_dist else -1.0


               # 전진을 멈추고 제자리에서 회전하여 벽을 옆으로 둠
               self.send_command(0.02, max_ang * 0.8 * turn_dir)
               time.sleep(0.1)
               continue


           # 2. 측면 분석
           left_min = np.min(lidar[70:110])
           right_min = np.min(lidar[250:290])
           side = "left" if left_min < right_min else "right"


           search_range = (60, 120) if side == "left" else (240, 300)
           side_data = lidar[search_range[0]:search_range[1]]
           actual_min_idx = np.argmin(side_data) + search_range[0]
           current_side_dist = lidar[actual_min_idx]


           # 3. 오차 계산 및 제어
           dist_error = current_side_dist - target_dist
           align_error = actual_min_idx - (90 if side == "left" else 270)
           mult = 1.0 if side == "left" else -1.0


           # 까딱거림 방지: 오차가 아주 작으면 조향을 줄임 (Deadzone)
           if abs(dist_error) < 0.02: dist_error = 0


           steer_cmd = (dist_error * kp_dist + align_error * kp_align) * mult
           final_steer = np.clip(steer_cmd, -max_ang * 1.2, max_ang * 1.2)


           # 전진 속도 최적화
           current_lin = max_lin * 0.5 if abs(dist_error) < 0.05 else max_lin * 0.5


           self.send_command(current_lin, final_steer)
           time.sleep(0.04)


       self.send_command(0, 0)


   def stop_mission(self):
       self.is_running = False
       self.cmd_lin, self.cmd_ang = 0.0, 0.0
       self.send_command(0, 0)
       self.log("🛑 강제 정지 명령 전송")


   def on_map_click(self, event):
       if self.line_mode:
           return


       if event.inaxes != self.ax or self.is_running: return


       if hasattr(self, 'press_x') and self.press_x is not None:
           dist = math.hypot(event.xdata - self.press_x, event.ydata - self.press_y)
           if dist > 0.1:  # 0.1m 이상 움직였다면 드래그로 간주하고 WP 안 찍음
               return


       now = time.time()


       # --- [좌클릭: WP 생성 또는 ROI 생성] ---
       if event.button == 1:
           # 더블 클릭 판정 (ROI 생성)
           if now - self.last_click_time < self.double_click_delay:
               self.log("🎯 ROI(목적지 구역) 설정")


               # 1. 직전 싱글 클릭으로 인해 생성된 마지막 WP 제거 (중복 방지)
               if self.waypoints:
                   self.waypoints.pop()
                   self.wp_markers.pop().remove()
                   self.wp_texts.pop().remove()
                   if hasattr(self, 'wp_lines') and self.wp_lines:
                       self.wp_lines.pop().remove()


               # 2. 기존 ROI가 있다면 제거 (1개만 유지)
               if self.roi_marker:
                   self.roi_marker.remove()
                   self.roi_text.remove()


               # 3. 새로운 ROI 생성
               self.roi_pos = (event.xdata, event.ydata)
               self.roi_marker, = self.ax.plot(event.xdata, event.ydata, 'ro', markersize=10, markerfacecolor='none',
                                               markeredgewidth=2)
               self.roi_text = self.ax.text(event.xdata, event.ydata + 0.5, "ROI GOAL", ha='center', color='red',
                                            fontweight='bold', fontsize=9)


           else:
               # 싱글 클릭 (WP 생성)
               new_wp = (event.xdata, event.ydata)


               # [핵심 추가] 선 리스트가 없으면 생성
               if not hasattr(self, 'wp_lines'):
                   self.wp_lines = []


               if self.waypoints:
                   prev_wp = self.waypoints[-1]
                   # 리스트 [x1, x2], [y1, y2] 형태로 plot
                   ln, = self.ax.plot([prev_wp[0], new_wp[0]], [prev_wp[1], new_wp[1]],
                                      'g--', linewidth=1, alpha=0.5)
                   self.wp_lines.append(ln)


               self.waypoints.append((event.xdata, event.ydata))
               m, = self.ax.plot(event.xdata, event.ydata, 'go', markersize=5)
               t = self.ax.text(event.xdata, event.ydata + 0.3, f"WP{len(self.waypoints)}", ha='center', color='green',
                                fontsize=8)
               self.wp_markers.append(m)
               self.wp_texts.append(t)


           self.last_click_time = now
           self.canvas.draw_idle()


       # --- [우클릭: 최근 순서대로 삭제 (WP 또는 ROI)] ---
       elif event.button == 3:
           # ROI가 가장 최근에 생성된 것인지 판단하기 위해 시간이나 플래그를 쓸 수 있지만,
           # 여기서는 "WP가 있으면 WP를 지우고, WP가 없으면 ROI를 지우는" 직관적인 스택 방식을 사용하거나
           # 단순히 둘 다 있는 경우 WP부터 지우도록 설계합니다.
           if self.waypoints:
               self.waypoints.pop()
               self.wp_markers.pop().remove()
               self.wp_texts.pop().remove()
               if hasattr(self, 'wp_lines') and self.wp_lines:
                   self.wp_lines.pop().remove()
               self.log("🗑 마지막 웨이포인트 삭제")
           elif self.roi_pos:
               self.roi_pos = None
               self.roi_marker.remove()
               self.roi_marker = None
               self.roi_text.remove()
               self.roi_text = None
               self.log("🗑 ROI 구역 삭제")


           self.canvas.draw_idle()


   def on_scroll(self, event):
       if event.inaxes != self.ax: return
       scale = 1 / self.zoom_scale if event.button == 'up' else self.zoom_scale
       cur_x, cur_y = self.ax.get_xlim(), self.ax.get_ylim()
       self.ax.set_xlim(event.xdata - (event.xdata - cur_x[0]) * scale, event.xdata + (cur_x[1] - event.xdata) * scale)
       self.ax.set_ylim(event.ydata - (event.ydata - cur_y[0]) * scale, event.ydata + (cur_y[1] - event.ydata) * scale)
       self.canvas.draw_idle()


   def start_roi_navigation(self):
       """ROI 구역으로 이동하는 주행 스레드 시작"""
       if self.roi_pos is None:
           self.log("⚠️ 설정된 ROI 구역이 없습니다. 지도를 더블 클릭하세요.")
           return


       self.is_running = True
       # ROI도 WP 주행과 동일한 로직(리스트 형태)으로 전달하여 실행
       threading.Thread(target=self.navigation_thread, args=([self.roi_pos], "ROI 구역 탐색"), daemon=True).start()


   def reset_zoom(self):
       self.ax.set_xlim(-25, 25)
       self.ax.set_ylim(-25, 25)
       self.canvas.draw_idle()


   def clear_obstacles(self):
       self.obstacle_points_x.clear()
       self.obstacle_points_y.clear()
       self.point_weights.clear()
       self.log("🧹 지도 장애물 데이터 초기화")


   def log(self, msg, level="INFO"):
       """화면 출력 + DB 저장 큐에 데이터 적재"""
       ts_full = time.strftime('%Y-%m-%d %H:%M:%S')  # DB 저장용 (년-월-일)
       ts_short = time.strftime('%H:%M:%S')  # UI 출력용 (시:분:초)


       # UI 출력
       self.log_text.insert(tk.END, f"[{ts_short}] {msg}\n")
       self.log_text.see(tk.END)


       # DB 저장 큐에 넣기 (비동기 처리)
       self.log_queue.put((ts_full, level, msg))


   def on_close(self):
       """프로그램 종료 시 DB 연결을 안전하게 닫음"""
       self.db_worker_running = False
       self.log_queue.put(None)  # 워커 스레드 종료 신호
       if self.db_conn:
           self.db_conn.close()
       self.destroy()


   def _init_log_db_mysql(self):
       """DB 생성 및 테이블 세팅"""
       try:
           # 1. 데이터베이스 자동 생성
           conn0 = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
                                   autocommit=True)
           cur0 = conn0.cursor()
           cur0.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB} DEFAULT CHARACTER SET utf8mb4")
           conn0.close()


           # 2. 실제 로그 테이블 생성
           self.db_conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
                                          database=MYSQL_DB, autocommit=True)
           self.db_cur = self.db_conn.cursor()
           self.db_cur.execute(f"""
               CREATE TABLE IF NOT EXISTS {MYSQL_TABLE} (
                   id BIGINT AUTO_INCREMENT PRIMARY KEY,
                   ts DATETIME NOT NULL,
                   level VARCHAR(10) DEFAULT 'INFO',
                   msg TEXT NOT NULL
               ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
           """)
           self.log("🗄️ 데이터베이스 연결 및 테이블 확인 완료")
       except Exception as e:
           print(f"DB 초기화 에러: {e}")


   def _start_log_db_worker_mysql(self):
       """UI를 멈추지 않게 별도 스레드에서 DB 저장 수행"""
       self.db_worker_running = True


       def worker():
           while self.db_worker_running:
               try:
                   # 0.5초마다 큐를 확인하여 로그 데이터가 있으면 가져옴
                   item = self.log_queue.get(timeout=0.5)
               except Empty:
                   continue


               if item is None: break  # 종료 신호


               ts_str, level, msg = item
               try:
                   self.db_cur.execute(
                       f"INSERT INTO {MYSQL_TABLE} (ts, level, msg) VALUES (%s, %s, %s)",
                       (ts_str, level, msg)
                   )
               except Exception as e:
                   print(f"DB 저장 실패: {e}")


       threading.Thread(target=worker, daemon=True).start()




if __name__ == "__main__":
   AbsoluteMapZoomController().mainloop()
