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
URL = "http://192.168.0.243:3333/control"
INTERVAL = 50

# --- 제어 및 안전 설정 ---
DEFAULT_LIN = 0.12
DEFAULT_ANG = 0.6
ANGLE_TOL = 0.05  # 각도 허용 오차 (라디안)
DIST_TOL = 0.05  # 거리 허용 오차 (미터)
LIDAR_SAMPLE_STEP = 2
LIDAR_HISTORY = 1500
LIDAR_NEAR_DIST = 5.0
LIDAR_STOP_DIST = 0.25  # 청소 중 장애물 감지 거리 (미터)
ROBOT_WIDTH = 0.4  # 청소 경로 간격 (미터)


class CleaningController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("거북이 청소 관제 시스템")
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

        # --- 청소 관련 변수 ---
        self.corners = []  # 구역 꼭짓점 4개
        self.cleaning_path = []  # 생성된 ㄹ자 경로
        self.cleaning_idx = 0  # 현재 목표 인덱스

        # 드래그 (Zoom/Pan)
        self.is_dragging = False
        self.press_x = None
        self.press_y = None

        self._create_layout()
        self._create_menubar()
        self._bind_events()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        threading.Thread(target=self.fetch_data_worker, daemon=True).start()
        self._after_id = self.after(INTERVAL, self.update_status)

    # --- UI 초기화 ---
    def _create_menubar(self):
        m = tk.Menu(self)

        # 설정 메뉴
        s = tk.Menu(m, tearoff=0)
        s.add_command(label="장애물 맵 초기화",
                      command=lambda: setattr(self, 'obstacle_points_x', []) or setattr(self, 'obstacle_points_y', []))
        m.add_cascade(label="설정", menu=s)

        # 청소 메뉴
        c = tk.Menu(m, tearoff=0)
        c.add_command(label="1. 현재 위치를 꼭짓점으로 저장", command=self.record_corner)
        c.add_command(label="2. 꼭짓점 초기화", command=self.reset_corners)
        c.add_separator()
        c.add_command(label="3. 청소 시작 (ㄹ자)", command=self.start_cleaning)
        c.add_command(label="4. 청소 중지", command=self.stop_mission)
        m.add_cascade(label="청소 제어", menu=c)

        self.config(menu=m)

    def _create_layout(self):
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)

        # 1. 맵 영역
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(-5, 5)
        self.ax.set_ylim(-5, 5)

        self.scat = self.ax.scatter([], [], s=1, c="#3498db", alpha=0.5)  # 장애물 점
        self.robot_dot, = self.ax.plot([], [], 'ro', markersize=8, zorder=10)  # 로봇 본체
        self.robot_dir, = self.ax.plot([], [], 'r-', linewidth=2, zorder=10)  # 로봇 헤딩

        # 청소 관련 플롯
        self.corner_plot, = self.ax.plot([], [], 'mx--', linewidth=1, label='Boundary')  # 경계선
        self.path_plot, = self.ax.plot([], [], 'g-', linewidth=1, alpha=0.7, label='Plan')  # 계획 경로
        self.target_dot, = self.ax.plot([], [], 'go', markersize=5)  # 현재 목표점

        self.canvas = FigureCanvasTkAgg(self.fig, master=main)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 2. 제어 패널
        ctrl = ttk.Frame(main, padding=10)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        self.pos_label = ttk.Label(ctrl, text="X: 0.00 Y: 0.00", font=('Courier', 12))
        self.pos_label.pack(pady=10)

        # 속도 제어
        ttk.Label(ctrl, text="청소 선속도").pack()
        self.lin_speed_var = tk.DoubleVar(value=DEFAULT_LIN)
        tk.Scale(ctrl, from_=0.05, to=0.3, resolution=0.01, orient=tk.HORIZONTAL, variable=self.lin_speed_var).pack(
            fill=tk.X)

        ttk.Label(ctrl, text="회전 속도").pack()
        self.ang_speed_var = tk.DoubleVar(value=DEFAULT_ANG)
        tk.Scale(ctrl, from_=0.1, to=1.5, resolution=0.05, orient=tk.HORIZONTAL, variable=self.ang_speed_var).pack(
            fill=tk.X)

        tk.Button(ctrl, text="⏹ 비상 정지", bg="red", fg="white", font=('bold'), command=self.stop_mission).pack(fill=tk.X,
                                                                                                             pady=20)

        self.log_text = tk.Text(ctrl, height=15, width=35, font=('Consolas', 9))
        self.log_text.pack()

    # --- 기본 기능 ---
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

                # 로봇 그리기
                self.robot_dot.set_data([self.rx], [self.ry])
                self.robot_dir.set_data([self.rx, self.rx + 0.4 * math.cos(self.ra)],
                                        [self.ry, self.ry + 0.4 * math.sin(self.ra)])

                # 라이다 그리기 (누적)
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

                # 꼭짓점 및 경로 그리기
                if self.corners:
                    cx, cy = zip(*self.corners)
                    # 닫힌 도형으로 표시
                    self.corner_plot.set_data(cx + (cx[0],), cy + (cy[0],))
                else:
                    self.corner_plot.set_data([], [])

                if self.cleaning_path:
                    px, py = zip(*self.cleaning_path)
                    self.path_plot.set_data(px, py)
                    # 현재 목표점 표시
                    if self.cleaning_idx < len(self.cleaning_path):
                        tx, ty = self.cleaning_path[self.cleaning_idx]
                        self.target_dot.set_data([tx], [ty])
                else:
                    self.path_plot.set_data([], [])
                    self.target_dot.set_data([], [])

                self.canvas.draw_idle()
            except Exception as e:
                print(e)

        self._after_id = self.after(INTERVAL, self.update_status)

    # --- Zoom & Pan ---
    def _bind_events(self):
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

    def on_press(self, event):
        if event.button == 2:  # 휠 클릭
            self.is_dragging = True
            self.press_x, self.press_y = event.xdata, event.ydata

    def on_motion(self, event):
        if self.is_dragging and event.xdata:
            dx, dy = event.xdata - self.press_x, event.ydata - self.press_y
            cur_xlim = self.ax.get_xlim()
            cur_ylim = self.ax.get_ylim()
            self.ax.set_xlim(cur_xlim[0] - dx, cur_xlim[1] - dx)
            self.ax.set_ylim(cur_ylim[0] - dy, cur_ylim[1] - dy)
            self.canvas.draw_idle()

    def on_release(self, event):
        self.is_dragging = False

    def on_scroll(self, event):
        if not event.xdata: return
        scale = 0.9 if event.button == 'up' else 1.1
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        w = (cur_xlim[1] - cur_xlim[0]) * scale
        h = (cur_ylim[1] - cur_ylim[0]) * scale
        rel_x = (event.xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0])
        rel_y = (event.ydata - cur_ylim[0]) / (cur_ylim[1] - cur_ylim[0])
        self.ax.set_xlim(event.xdata - w * rel_x, event.xdata + w * (1 - rel_x))
        self.ax.set_ylim(event.ydata - h * rel_y, event.ydata + h * (1 - rel_y))
        self.canvas.draw_idle()

    # --- 청소(경로 생성) 로직 ---
    def record_corner(self):
        self.corners.append((self.rx, self.ry))
        self.log(f"📍 꼭짓점 {len(self.corners)} 저장: ({self.rx:.2f}, {self.ry:.2f})")
        if len(self.corners) > 4:
            self.log("⚠️ 꼭짓점은 4개까지만 저장됩니다. (초기화 필요)")
            self.corners.pop()

    def reset_corners(self):
        self.corners = []
        self.cleaning_path = []
        self.log("🗑 꼭짓점 데이터 초기화됨")

    def generate_zigzag_path(self):
        if len(self.corners) != 4:
            self.log("❌ 꼭짓점 4개가 필요합니다.")
            return False

        # P0-P3 (왼쪽 변), P1-P2 (오른쪽 변)으로 가정
        # P0(시작) -> P1 방향으로 진행
        p0 = np.array(self.corners[0])
        p1 = np.array(self.corners[1])
        p2 = np.array(self.corners[2])
        p3 = np.array(self.corners[3])

        # 왼쪽 벡터와 오른쪽 벡터 길이 계산
        left_vec = p3 - p0
        right_vec = p2 - p1

        len_left = np.linalg.norm(left_vec)

        # 몇 번 왕복할지 계산 (높이 / 로봇폭)
        steps = int(len_left / ROBOT_WIDTH)

        path = []
        for i in range(steps + 1):
            t = i / steps
            # 보간법으로 양쪽 변의 등분점 찾기
            start_p = p0 + t * left_vec
            end_p = p1 + t * right_vec

            # 지그재그 패턴
            if i % 2 == 0:
                path.append(tuple(start_p))  # 왼쪽 -> 오른쪽
                path.append(tuple(end_p))
            else:
                path.append(tuple(end_p))  # 오른쪽 -> 왼쪽
                path.append(tuple(start_p))

        self.cleaning_path = path
        self.cleaning_idx = 0
        self.log(f"✅ 경로 생성 완료: 총 {len(path)}개 웨이포인트")
        return True

    # --- 자율 주행 로직 ---
    def stop_mission(self):
        self.is_running = False
        self.send_command(0, 0)
        self.log("🛑 미션 중지")

    def start_cleaning(self):
        if not self.corners:
            self.log("❌ 꼭짓점이 설정되지 않았습니다.")
            return

        if not self.cleaning_path:
            if not self.generate_zigzag_path(): return

        self.is_running = True
        threading.Thread(target=self.cleaning_thread, daemon=True).start()

    def cleaning_thread(self):
        self.log("🧹 청소 시작!")

        while self.is_running and self.cleaning_idx < len(self.cleaning_path):
            target = self.cleaning_path[self.cleaning_idx]
            self.log(f"➡️ 이동 중: WP[{self.cleaning_idx}] {target[0]:.2f}, {target[1]:.2f}")

            # 1. 제자리 회전
            if not self.rotate_to(target):
                break

            # 2. 직선 주행 (장애물 감지 포함)
            arrived, obstacle = self.move_straight_to(target)

            if obstacle:
                self.log("🚧 장애물 감지! 현재 라인 스킵")
                # 장애물 발견 시: 후진 살짝 하고 다음 포인트로 넘어감
                self.send_command(-0.1, 0)
                time.sleep(1.0)
                self.send_command(0, 0)

                # 현재 목표가 짝수 인덱스(라인 끝)라면 스킵하고 다음 홀수(다음 라인 시작)로
                # 이미 홀수라면 그냥 다음으로
                self.cleaning_idx += 1
            elif arrived:
                self.cleaning_idx += 1
            else:
                break  # 강제 중지 등

            time.sleep(0.5)  # 포인트 간 잠시 대기

        self.send_command(0, 0)
        self.is_running = False
        self.log("✨ 청소 종료")

    def rotate_to(self, target):
        """ 목표 지점을 향해 회전 """
        tx, ty = target
        while self.is_running:
            dx = tx - self.rx
            dy = ty - self.ry
            target_ang = math.atan2(dy, dx)

            diff = (target_ang - self.ra + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) < ANGLE_TOL:
                self.send_command(0, 0)
                return True

            spd = np.clip(1.5 * diff, -self.ang_speed_var.get(), self.ang_speed_var.get())
            if abs(spd) < 0.2: spd = 0.2 * np.sign(spd)

            self.send_command(0, spd)
            time.sleep(0.05)
        return False

    def move_straight_to(self, target):
        """ 직선 주행하며 장애물 감지. (도착여부, 장애물여부) 반환 """
        tx, ty = target
        while self.is_running:
            dx = tx - self.rx
            dy = ty - self.ry
            dist = math.hypot(dx, dy)

            # 도착 확인
            if dist < DIST_TOL:
                self.send_command(0, 0)
                return True, False

            # 장애물 감지 (전방 60도 부채꼴 내 장애물 확인)
            if self.check_obstacle_front():
                self.send_command(0, 0)
                return False, True  # 장애물 있음

            # 조향 보정 (이동 중 각도 틀어짐 보정)
            target_ang = math.atan2(dy, dx)
            diff = (target_ang - self.ra + math.pi) % (2 * math.pi) - math.pi
            ang_corr = np.clip(2.0 * diff, -0.5, 0.5)

            lin_spd = self.lin_speed_var.get()
            # 목표에 가까워지면 감속
            if dist < 0.2: lin_spd *= 0.5

            self.send_command(lin_spd, ang_corr)
            time.sleep(0.05)

        return False, False

    def check_obstacle_front(self):
        """ 전방의 장애물 확인 """
        if len(self.latest_lidar) == 0: return False

        # 전방 -30도 ~ +30도 범위 인덱스 추출
        num_p = len(self.latest_lidar)
        fov = np.deg2rad(40)  # 시야각

        # 인덱스 계산 (라이다가 0도가 정면이라 가정)
        # 실제 라이다 장착 방향에 따라 인덱스 조정 필요할 수 있음
        # 여기서는 0도가 로봇 정면이라 가정

        threshold = LIDAR_STOP_DIST

        # 배열을 순회하며 전방 데이터 확인
        # (간단하게 전방 1/8 영역을 확인)
        front_cnt = int(num_p * (40 / 360))
        mid = 0  # 0도가 정면 시작점 (보통 라이다마다 다름. A1/A2는 보통 정면이 0이거나 180)

        # 0도 기준 좌우 데이터 가져오기 (배열 인덱싱 처리)
        # 여기서는 단순하게 전체 스캔 중 거리가 가깝고 각도가 전방인 것 필터링

        angles = np.linspace(0, 2 * np.pi, num_p, endpoint=False)
        # 로봇 기준 상대 각도로 변환 필요 없이, 라이다 데이터 순서가 로봇 기준임

        # 각도가 0~pi/6 혹은 2pi-pi/6 ~ 2pi 인 데이터 (전방 60도)
        mask = (angles < fov / 2) | (angles > 2 * np.pi - fov / 2)
        front_dists = self.latest_lidar[mask]

        # 유효 거리(0.05m 이상) 중 충돌 위험 거리 이하가 있는지
        valid_mask = (front_dists > 0.05) & (front_dists < threshold)
        if np.any(valid_mask):
            return True

        return False


if __name__ == "__main__":
    app = CleaningController()
    app.mainloop()