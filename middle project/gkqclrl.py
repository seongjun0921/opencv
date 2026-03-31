import tkinter as tk
from tkinter import ttk
import math
import time
import requests
import numpy as np
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ================= 설정 =================
URL = "http://192.168.0.243:4110/control"
INTERVAL = 50

# --- 제어 및 안전 설정 ---
DEFAULT_LIN = 0.12
DEFAULT_ANG = 0.6
ANGLE_TOL = 0.05  # 각도 허용 오차 (라디안)
DIST_TOL = 0.05  # 거리 허용 오차 (미터)
LIDAR_SAMPLE_STEP = 2
LIDAR_HISTORY = 1500
LIDAR_NEAR_DIST = 5.0
LIDAR_STOP_DIST = 0.25  # 청소 중 장애물 감지 거리
WALL_DETECT_DIST = 0.35  # 자동 맵핑 시 벽 감지 거리 (이보다 가까우면 꼭짓점 판단)
ROBOT_WIDTH = 0.4  # 청소 경로 간격


class CleaningController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("거북이 청소 & 자동 맵핑 시스템")
        self.geometry("1200x950")

        # --- 통신 및 상태 ---
        self.session = requests.Session()
        self.current_telemetry = None
        self.is_running = False
        self._after_id = None

        # 로봇 상태
        self.rx, self.ry, self.ra = 0.0, 0.0, 0.0
        self.offset_x, self.offset_y = 0.0, 0.0

        # 지도 및 라이다 데이터
        self.obstacle_points_x = []
        self.obstacle_points_y = []
        self.latest_lidar = []

        # --- 청소/맵핑 관련 변수 ---
        self.corners = []  # 구역 꼭짓점
        self.cleaning_path = []  # 생성된 경로
        self.cleaning_idx = 0

        # UI 생성
        self._create_layout()
        self._create_menubar()
        self._bind_events()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        threading.Thread(target=self.fetch_data_worker, daemon=True).start()
        self._after_id = self.after(INTERVAL, self.update_status)

    def _create_menubar(self):
        m = tk.Menu(self)

        # 설정 메뉴
        s = tk.Menu(m, tearoff=0)
        s.add_command(label="장애물 맵 초기화",
                      command=lambda: setattr(self, 'obstacle_points_x', []) or setattr(self, 'obstacle_points_y', []))
        m.add_cascade(label="설정", menu=s)

        # 맵핑 및 청소 메뉴
        c = tk.Menu(m, tearoff=0)
        c.add_command(label="[자동] 벽 따라 맵핑 시작", command=self.start_auto_mapping)
        c.add_separator()
        c.add_command(label="[수동] 현재 위치 꼭짓점 저장", command=self.record_corner)
        c.add_command(label="꼭짓점 초기화", command=self.reset_corners)
        c.add_separator()
        c.add_command(label="청소 시작 (ㄹ자)", command=self.start_cleaning)
        c.add_command(label="작업 중지", command=self.stop_mission)
        m.add_cascade(label="작업 제어", menu=c)

        self.config(menu=m)

    def _create_layout(self):
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)

        # Matplotlib Canvas
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(-5, 5)
        self.ax.set_ylim(-5, 5)

        self.scat = self.ax.scatter([], [], s=1, c="#3498db", alpha=0.5)
        self.robot_dot, = self.ax.plot([], [], 'ro', markersize=8, zorder=10)
        self.robot_dir, = self.ax.plot([], [], 'r-', linewidth=2, zorder=10)

        self.corner_plot, = self.ax.plot([], [], 'mx--', linewidth=1, label='Boundary')
        self.path_plot, = self.ax.plot([], [], 'g-', linewidth=1, alpha=0.7, label='Plan')
        self.target_dot, = self.ax.plot([], [], 'go', markersize=5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=main)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Control Panel
        ctrl = ttk.Frame(main, padding=10)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        self.pos_label = ttk.Label(ctrl, text="X: 0.00 Y: 0.00", font=('Courier', 12))
        self.pos_label.pack(pady=10)

        ttk.Label(ctrl, text="선속도").pack()
        self.lin_speed_var = tk.DoubleVar(value=DEFAULT_LIN)
        tk.Scale(ctrl, from_=0.05, to=0.3, resolution=0.01, orient=tk.HORIZONTAL, variable=self.lin_speed_var).pack(
            fill=tk.X)

        ttk.Label(ctrl, text="각속도").pack()
        self.ang_speed_var = tk.DoubleVar(value=DEFAULT_ANG)
        tk.Scale(ctrl, from_=0.1, to=1.5, resolution=0.05, orient=tk.HORIZONTAL, variable=self.ang_speed_var).pack(
            fill=tk.X)

        tk.Button(ctrl, text="⏹ 비상 정지", bg="red", fg="white", font=('bold'), command=self.stop_mission).pack(fill=tk.X,
                                                                                                             pady=20)

        self.log_text = tk.Text(ctrl, height=15, width=35, font=('Consolas', 9))
        self.log_text.pack()

        # Zoom/Pan variables
        self.is_dragging = False
        self.press_x, self.press_y = None, None

    # --- System & UI Events ---
    def log(self, msg):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)

    def on_close(self):
        self.is_running = False
        if self._after_id: self.after_cancel(self._after_id)
        plt.close('all')
        self.session.close()
        self.quit()
        self.destroy()

    def fetch_data_worker(self):
        while True:
            try:
                res = self.session.get(URL, timeout=0.1).json()
                self.current_telemetry = res
            except:
                pass
            time.sleep(0.04)

    def send_command(self, lin, ang):
        def _send():
            try:
                self.session.get(f"{URL}?lin={lin:.2f}&ang={ang:.2f}", timeout=0.05)
            except:
                pass

        threading.Thread(target=_send, daemon=True).start()

    def update_status(self):
        if not self.winfo_exists(): return
        if self.current_telemetry:
            try:
                data = self.current_telemetry
                odom = data["p"]
                self.rx, self.ry, self.ra = odom['x'] + self.offset_x, odom['y'] + self.offset_y, odom['a']
                self.latest_lidar = np.array(data["s"], dtype=float) / 100.0

                self.pos_label.config(text=f"X: {self.rx:.2f} Y: {self.ry:.2f}\nA: {self.ra:.2f}")

                # Draw Robot
                self.robot_dot.set_data([self.rx], [self.ry])
                self.robot_dir.set_data([self.rx, self.rx + 0.4 * math.cos(self.ra)],
                                        [self.ry, self.ry + 0.4 * math.sin(self.ra)])

                # Draw Lidar
                num_p = len(self.latest_lidar)
                angles = np.linspace(0, 2 * np.pi, num_p, endpoint=False)
                idx = np.arange(0, num_p, LIDAR_SAMPLE_STEP)
                dists = self.latest_lidar[idx]
                v = (dists > 0.05) & (dists < LIDAR_NEAR_DIST)

                wx = self.rx + dists[v] * np.cos(angles[idx][v] + self.ra)
                wy = self.ry + dists[v] * np.sin(angles[idx][v] + self.ra)

                self.obstacle_points_x.extend(wx)
                self.obstacle_points_y.extend(wy)
                if len(self.obstacle_points_x) > LIDAR_HISTORY:
                    self.obstacle_points_x = self.obstacle_points_x[-LIDAR_HISTORY:]
                    self.obstacle_points_y = self.obstacle_points_y[-LIDAR_HISTORY:]

                self.scat.set_offsets(np.c_[self.obstacle_points_x, self.obstacle_points_y])

                # Draw Corners & Path
                if self.corners:
                    cx, cy = zip(*self.corners)
                    if len(self.corners) == 4:  # 닫힌 사각형
                        self.corner_plot.set_data(cx + (cx[0],), cy + (cy[0],))
                    else:
                        self.corner_plot.set_data(cx, cy)
                else:
                    self.corner_plot.set_data([], [])

                if self.cleaning_path:
                    px, py = zip(*self.cleaning_path)
                    self.path_plot.set_data(px, py)
                    if self.cleaning_idx < len(self.cleaning_path):
                        tx, ty = self.cleaning_path[self.cleaning_idx]
                        self.target_dot.set_data([tx], [ty])
                else:
                    self.path_plot.set_data([], [])
                    self.target_dot.set_data([], [])

                self.canvas.draw_idle()
            except Exception as e:
                pass
        self._after_id = self.after(INTERVAL, self.update_status)

    # --- Interaction ---
    def _bind_events(self):
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

    def on_press(self, event):
        if event.button == 2:
            self.is_dragging = True
            self.press_x, self.press_y = event.xdata, event.ydata

    def on_motion(self, event):
        if self.is_dragging and event.xdata:
            dx, dy = event.xdata - self.press_x, event.ydata - self.press_y
            cur_xlim, cur_ylim = self.ax.get_xlim(), self.ax.get_ylim()
            self.ax.set_xlim(cur_xlim[0] - dx, cur_xlim[1] - dx)
            self.ax.set_ylim(cur_ylim[0] - dy, cur_ylim[1] - dy)
            self.canvas.draw_idle()

    def on_release(self, event):
        self.is_dragging = False

    def on_scroll(self, event):
        if not event.xdata: return
        scale = 0.9 if event.button == 'up' else 1.1
        cur_xlim, cur_ylim = self.ax.get_xlim(), self.ax.get_ylim()
        w, h = (cur_xlim[1] - cur_xlim[0]) * scale, (cur_ylim[1] - cur_ylim[0]) * scale
        rx, ry = (event.xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0]), (event.ydata - cur_ylim[0]) / (
                    cur_ylim[1] - cur_ylim[0])
        self.ax.set_xlim(event.xdata - w * rx, event.xdata + w * (1 - rx))
        self.ax.set_ylim(event.ydata - h * ry, event.ydata + h * (1 - ry))
        self.canvas.draw_idle()

    # ================= [추가] 자동 맵핑 로직 =================
    def start_auto_mapping(self):
        self.corners = []
        self.cleaning_path = []
        self.is_running = True
        self.log("🤖 자동 맵핑 시작: 벽을 따라 4개의 꼭짓점을 찾습니다.")
        threading.Thread(target=self.auto_mapping_thread, daemon=True).start()

    def auto_mapping_thread(self):
        self.corners = []
        self.log("🤖 [정밀 맵핑] 우측 벽을 따라 이동하며 꼭짓점을 찾습니다.")

        # 주행 파라미터
        TARGET_DIST = 0.25  # 벽 유지 거리
        KP = 3.5  # 조향 민감도

        for i in range(4):
            if not self.is_running: break
            self.log(f"📍 {i + 1}번째 벽 추적 및 꼭짓점 탐색 중...")

            while self.is_running:
                # 1. 센서 데이터 샘플링
                d_front = self.get_dist_at(0, 15)  # 정면 (좁게)
                d_fr = self.get_dist_at(-45, 20)  # 우전방
                d_right = self.get_dist_at(-90, 15)  # 우측 수직

                # 2. 꼭짓점 판단 조건 (정면이 막히면 해당 지점을 꼭짓점으로 기록)
                if d_front < WALL_DETECT_DIST:
                    self.send_command(0, 0)
                    time.sleep(0.8)  # 물리적 관성 정지 대기
                    self.record_corner()
                    break

                # 3. 우측 벽타기 주행 로직 (P-제어)
                lin = self.lin_speed_var.get()
                ang = 0.0

                if d_right < 1.2:  # 우측에 벽이 감지될 때
                    error = TARGET_DIST - d_right
                    ang = error * KP

                    # 우전방(d_fr)이 벽에 너무 가까워지면(안쪽 코너 진입 시) 미리 좌회전 보정
                    if d_fr < TARGET_DIST:
                        ang += 0.3
                else:
                    # 벽을 놓친 경우 (바깥 코너 등) 우회전하며 탐색
                    ang = -0.5
                    lin = 0.1

                # 속도 최적화 (회전 시 감속)
                actual_lin = lin - (abs(ang) * 0.05)
                self.send_command(max(0.05, actual_lin), np.clip(ang, -1.0, 1.0))
                time.sleep(0.05)

            # 4. 다음 면을 향해 정확히 90도 회전
            if i < 3 and self.is_running:
                self.log("↩️ 모서리 회전...")
                # 현재 각도 기준으로 정확히 왼쪽으로 90도(+pi/2) 회전
                target_ang = self.ra + (math.pi / 2)
                self.rotate_to_angle_absolute(target_ang)
                time.sleep(0.5)

        self.log("✅ 정밀 맵핑 완료!")
        self.send_command(0, 0)
        self.is_running = False

    def get_front_min_dist(self):
        """ 전방 30도 부채꼴 내의 최소 거리 반환 """
        if len(self.latest_lidar) == 0: return 999.9

        num_p = len(self.latest_lidar)
        fov = np.deg2rad(30)  # 전방 시야각
        angles = np.linspace(0, 2 * np.pi, num_p, endpoint=False)

        # 전방 부채꼴 인덱스 마스킹
        mask = (angles < fov / 2) | (angles > 2 * np.pi - fov / 2)
        front_dists = self.latest_lidar[mask]

        # 유효 데이터(0.05m 이상) 중 최소값
        valid = front_dists[front_dists > 0.05]
        if len(valid) == 0: return 999.9

        return np.min(valid)

    def rotate_to_angle_absolute(self, target_rad):
        """ 절대 각도(rad)로 회전 """
        while self.is_running:
            diff = (target_rad - self.ra + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) < ANGLE_TOL:
                self.send_command(0, 0)
                break

            spd = np.clip(1.5 * diff, -self.ang_speed_var.get(), self.ang_speed_var.get())
            if abs(spd) < 0.2: spd = 0.2 * np.sign(spd)  # 최소 속도 보장
            self.send_command(0, spd)
            time.sleep(0.05)

    # ================= [기존] 청소 로직 유지 =================
    def record_corner(self):
        self.corners.append((self.rx, self.ry))
        self.log(f"📍 꼭짓점 {len(self.corners)} 저장: ({self.rx:.2f}, {self.ry:.2f})")
        if len(self.corners) > 4: self.corners.pop()

    def reset_corners(self):
        self.corners = []
        self.cleaning_path = []
        self.log("🗑 꼭짓점 데이터 초기화됨")

    def generate_zigzag_path(self):
        if len(self.corners) != 4:
            self.log("❌ 꼭짓점 4개가 필요합니다.")
            return False
        p0, p1, p2, p3 = [np.array(c) for c in self.corners]
        left_vec, right_vec = p3 - p0, p2 - p1
        steps = int(np.linalg.norm(left_vec) / ROBOT_WIDTH)
        path = []
        for i in range(steps + 1):
            t = i / steps
            start, end = p0 + t * left_vec, p1 + t * right_vec
            if i % 2 == 0:
                path.extend([tuple(start), tuple(end)])
            else:
                path.extend([tuple(end), tuple(start)])
        self.cleaning_path = path
        self.cleaning_idx = 0
        self.log(f"✅ 경로 생성 완료: {len(path)} 포인트")
        return True

    def stop_mission(self):
        self.is_running = False
        self.send_command(0, 0)
        self.log("🛑 미션 중지")

    def start_cleaning(self):
        if not self.corners:
            self.log("❌ 꼭짓점 없음")
            return
        if not self.cleaning_path:
            if not self.generate_zigzag_path(): return
        self.is_running = True
        threading.Thread(target=self.cleaning_thread, daemon=True).start()

    def cleaning_thread(self):
        self.log("🧹 청소 시작!")
        while self.is_running and self.cleaning_idx < len(self.cleaning_path):
            target = self.cleaning_path[self.cleaning_idx]
            if not self.rotate_to(target): break
            arrived, obs = self.move_straight_to(target)
            if obs:
                self.log("🚧 장애물! 라인 스킵")
                self.send_command(-0.1, 0)
                time.sleep(1.0)
                self.send_command(0, 0)
                self.cleaning_idx += 1
            elif arrived:
                self.cleaning_idx += 1
            else:
                break
            time.sleep(0.5)
        self.send_command(0, 0)
        self.is_running = False
        self.log("✨ 청소 종료")

    def rotate_to(self, target):
        tx, ty = target
        return self.rotate_to_angle_absolute(math.atan2(ty - self.ry, tx - self.rx)) or True

    def move_straight_to(self, target):
        tx, ty = target
        while self.is_running:
            dx, dy = tx - self.rx, ty - self.ry
            dist = math.hypot(dx, dy)
            if dist < DIST_TOL:
                self.send_command(0, 0)
                return True, False
            if self.get_front_min_dist() < LIDAR_STOP_DIST:  # 기존 check_obstacle_front 대체
                self.send_command(0, 0)
                return False, True

            target_ang = math.atan2(dy, dx)
            diff = (target_ang - self.ra + math.pi) % (2 * math.pi) - math.pi
            lin_spd = self.lin_speed_var.get() * (0.5 if dist < 0.2 else 1.0)
            self.send_command(lin_spd, np.clip(2.0 * diff, -0.5, 0.5))
            time.sleep(0.05)
        return False, False


if __name__ == "__main__":
    app = CleaningController()
    app.mainloop()