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
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "0000"
MYSQL_DB = "robot_control"
MYSQL_TABLE = "system_logs"

# ================= 설정 =================
URL = "http://192.168.0.243:4110/control"
INTERVAL = 50

DEFAULT_LIN = 0.12
DEFAULT_ANG = 0.6
WP_TOL = 0.15
DIST_NEAR_WP = 0.40
ANGLE_TOL = 0.01  # 약 0.5도

# --- 안전 및 라이다 설정 ---
FRONT_STOP_DIST = 0.15
LIDAR_SAMPLE_STEP = 2
LIDAR_HISTORY = 1500
LIDAR_NEAR_DIST = 5.0


class AbsoluteMapZoomController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("거북이 관제 시스템 - 로봇청소기 모드")
        self.geometry("1200x950")

        self.session = requests.Session()
        self.current_telemetry = None

        self.roi_pos = None
        self.roi_marker = None
        self.roi_text = None

        self.last_click_time = 0
        self.double_click_delay = 0.3

        self.is_running = False
        self.waypoints = []
        self.wp_markers = []
        self.wp_texts = []
        self.wp_lines = []

        # --- 청소기 기능 관련 변수 ---
        self.area_vertices = []  # 탐색된 꼭짓점
        self.zigzag_path = []  # 생성된 ㄹ자 경로
        self.vertex_plots = []  # 지도 표시용

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

        self.is_dragging = False
        self.press_x = None
        self.press_y = None

        self._create_layout()
        self._create_menubar()

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('button_press_event', self.on_map_click)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        self._init_log_db_mysql()
        self._start_log_db_worker_mysql()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        threading.Thread(target=self.fetch_data_worker, daemon=True).start()
        self.after(INTERVAL, self.update_status)

    # ---------------------------------------------------------
    # [새로 추가된 기능: 로봇 청소기 로직]
    # ---------------------------------------------------------
    def start_auto_mapping(self):
        """1단계: 우측 벽을 따라가며 꼭짓점 탐색"""
        if self.is_running: return
        self.is_running = True
        self.area_vertices = []
        # 현재 위치를 첫 번째 꼭짓점으로 시작
        self.area_vertices.append((self.rx, self.ry))
        threading.Thread(target=self.follow_wall_and_mapping_thread, daemon=True).start()

    def follow_wall_and_mapping_thread(self, target_dist=0.30):
        self.log("🧹 외곽 탐색 및 꼭짓점 추출 시작 (우측 벽 타기)")
        start_time = time.time()
        last_vertex_pos = (self.rx, self.ry)

        while self.is_running:
            if self.latest_lidar is None or len(self.latest_lidar) == 0:
                time.sleep(0.05);
                continue

            lidar = np.array(self.latest_lidar)
            lidar = np.where(lidar > 0.1, lidar, 3.5)  # 노이즈 제거

            # 1. 정면 및 우측 거리 체크
            front_min = np.min(np.concatenate([lidar[-20:], lidar[:20]]))
            right_min = np.min(lidar[240:300])  # 로봇 기준 우측 (270도 부근)

            # 2. 꼭짓점 판단: 정면에 벽이 나타나서 회전이 필요한 경우
            dist_from_last = math.hypot(self.rx - last_vertex_pos[0], self.ry - last_vertex_pos[1])
            if front_min < 0.45 and dist_from_last > 0.7:
                self.area_vertices.append((self.rx, self.ry))
                last_vertex_pos = (self.rx, self.ry)
                self.log(f"📍 꼭짓점 기록: ({self.rx:.2f}, {self.ry:.2f})")

                # 우측 벽을 계속 타기 위해 왼쪽으로 90도 회전
                self.send_command(0, 0)
                time.sleep(0.3)
                self.align_angle(self.ra + math.pi / 2)
                continue

            # 3. 우측 벽 유지 제어 (P-제어)
            error = right_min - target_dist
            steer = np.clip(error * 2.5, -self.ang_speed_var.get(), self.ang_speed_var.get())

            # 정면이 너무 가깝지 않으면 전진
            lin = self.lin_speed_var.get() * 0.7 if front_min > 0.4 else 0.02
            self.send_command(lin, steer)

            # 4. 종료 조건: 한 바퀴를 돌아 시작점 근처로 온 경우 (최소 꼭짓점 3개 이상)
            if len(self.area_vertices) >= 3:
                dist_to_start = math.hypot(self.rx - self.area_vertices[0][0], self.ry - self.area_vertices[0][1])
                if dist_to_start < 0.4 and (time.time() - start_time > 20):
                    self.log("✅ 외곽 탐색 완료! 영역을 닫습니다.")
                    break

            time.sleep(0.05)

        self.send_command(0, 0)
        self.is_running = False
        self.generate_zigzag_path()

    def generate_zigzag_path(self):
        """탐색된 꼭짓점 기반 ㄹ자 경로 생성"""
        if len(self.area_vertices) < 3:
            self.log("⚠️ 꼭짓점이 부족하여 경로를 생성할 수 없습니다.")
            return

        def start_cleaning_mission(self):
            """청소 미션 전체 프로세스 시작"""
            if self.is_running: return
            self.is_running = True
            threading.Thread(target=self.cleaning_master_thread, daemon=True).start()

        def cleaning_master_thread(self):
            # 1단계: 벽 탐색 및 외곽 맵핑 (성공 시 True 반환)
            if self.follow_wall_and_mapping():
                # 2단계: ㄹ자 경로 생성
                self.generate_zigzag_path()
                # 3단계: ㄹ자 주행 시작
                if self.zigzag_path:
                    self.log("🏁 맵핑 완료. ㄹ자 청소를 시작합니다.")
                    self.navigation_thread(self.zigzag_path, "ㄹ자 청소 주행")

        def follow_wall_and_mapping(self, target_dist=0.35):
            self.log("🚀 [1단계] 벽 탐색 시작: 정면 벽을 향해 이동합니다.")
            self.area_vertices = []

            # [벽 찾기] 정면 벽이 보일 때까지 전진
            while self.is_running:
                if self.latest_lidar is None or len(self.latest_lidar) == 0:
                    time.sleep(0.1);
                    continue

                lidar = self.latest_lidar
                # 정면(0도 근처) 거리 확인
                front_dist = self.get_sector_dist(lidar, -15, 15)

                if front_dist < 0.45:
                    self.log("🧱 벽 발견! 우측으로 벽을 두기 위해 회전합니다.")
                    self.send_command(0, 0)
                    time.sleep(0.5)
                    # 현재 각도에서 좌측으로 90도 회전하여 벽을 우측(270도 방향)에 위치시킴
                    self.align_angle(self.ra + math.pi / 2)
                    break
                self.send_command(0.1, 0)
                time.sleep(0.05)

            # [벽 따라가며 꼭짓점 기록]
            self.log("📍 우측 벽 따라가기 및 코너 탐색 시작")
            start_pos = (self.rx, self.ry)
            self.area_vertices.append(start_pos)
            start_time = time.time()

            while self.is_running:
                lidar = self.latest_lidar
                front_dist = self.get_sector_dist(lidar, -15, 15)
                right_dist = self.get_sector_dist(lidar, 250, 290)  # 우측 센서 범위

                # 코너 판단 (정면에 벽이 나타나면 새로운 꼭짓점 기록 후 회전)
                dist_from_last = math.hypot(self.rx - self.area_vertices[-1][0], self.ry - self.area_vertices[-1][1])
                if front_dist < 0.40 and dist_from_last > 0.6:
                    self.area_vertices.append((self.rx, self.ry))
                    self.log(f"📍 꼭짓점 기록: ({self.rx:.2f}, {self.ry:.2f})")
                    self.send_command(0, 0)
                    time.sleep(0.3)
                    self.align_angle(self.ra + math.pi / 2)
                    continue

                # 우측 벽 유지 제어 (P-제어)
                if right_dist > 0.8:  # 벽이 너무 멀어지면 우측으로 회전하며 탐색
                    steer = -0.4
                else:
                    error = right_dist - target_dist
                    steer = np.clip(error * 2.5, -0.6, 0.6)

                self.send_command(0.1, steer)

                # 복귀 판단 (최소 꼭짓점 3개 이상 후 시작점 근처 도착)
                if len(self.area_vertices) >= 3:
                    dist_to_start = math.hypot(self.rx - start_pos[0], self.ry - start_pos[1])
                    if dist_to_start < 0.5 and (time.time() - start_time > 20):
                        self.log("✅ 외곽 탐색 완료")
                        break
                time.sleep(0.05)

            self.send_command(0, 0)
            return True

        def get_sector_dist(self, lidar, start_deg, end_deg):
            """라이다의 특정 각도 구간 내 최소 거리 반환 (음수 각도 처리)"""
            n = len(lidar)
            indices = []
            for d in range(start_deg, end_deg):
                indices.append(int((d % 360) * (n / 360.0)))
            vals = lidar[indices]
            valid = vals[vals > 0.05]
            return np.min(valid) if len(valid) > 0 else 5.0

        def generate_zigzag_path(self):
            """탐색된 꼭짓점들의 Boundary 내부에 ㄹ자 경로 생성"""
            if len(self.area_vertices) < 3: return
            v = np.array(self.area_vertices)
            min_x, max_x = v[:, 0].min(), v[:, 0].max()
            min_y, max_y = v[:, 1].min(), v[:, 1].max()

            step = 0.4  # ㄹ자 간격
            path = []
            curr_y = min_y + 0.2
            direction = 1

            while curr_y < max_y:
                if direction == 1:
                    path.append((min_x + 0.2, curr_y))
                    path.append((max_x - 0.2, curr_y))
                else:
                    path.append((max_x - 0.2, curr_y))
                    path.append((min_x + 0.2, curr_y))
                curr_y += step
                direction *= -1

            self.zigzag_path = path
            self.log(f"🗺 ㄹ자 경로 생성 완료: {len(path)}개 지점")
        v_arr = np.array(self.area_vertices)
        min_x, max_x = v_arr[:, 0].min(), v_arr[:, 0].max()
        min_y, max_y = v_arr[:, 1].min(), v_arr[:, 1].max()

        step = 0.4  # 청소기 겹침폭 (ㄹ자 간격)
        path = []
        curr_y = min_y + 0.2
        direction = 1  # 1: 우측행, -1: 좌측행

        while curr_y < max_y:
            if direction == 1:
                path.append((min_x + 0.2, curr_y))
                path.append((max_x - 0.2, curr_y))
            else:
                path.append((max_x - 0.2, curr_y))
                path.append((min_x + 0.2, curr_y))
            curr_y += step
            direction *= -1

        self.zigzag_path = path
        self.waypoints = path  # 기존 WP 시스템에 태움
        self.log(f"🗺 ㄹ자 경로 생성 완료: {len(path)}개 지점")

    def start_zigzag_cleaning(self):
        """2단계: 생성된 ㄹ자 경로로 주행"""
        if not self.zigzag_path:
            self.log("⚠️ 먼저 외곽 탐색을 수행하세요.")
            return
        self.is_running = True
        threading.Thread(target=self.navigation_thread, args=(self.zigzag_path, "ㄹ자 청소"), daemon=True).start()

    # ---------------------------------------------------------
    # [기존 핵심 로직 유지]
    # ---------------------------------------------------------
    def on_press(self, event):
        if event.inaxes != self.ax: return
        if event.button == 2:
            self.is_dragging = True
            self.press_x = event.xdata
            self.press_y = event.ydata

    def on_motion(self, event):
        if not self.is_dragging or event.inaxes != self.ax: return
        dx = event.xdata - self.press_x
        dy = event.ydata - self.press_y
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        self.ax.set_xlim(cur_xlim[0] - dx, cur_xlim[1] - dx)
        self.ax.set_ylim(cur_ylim[0] - dy, cur_ylim[1] - dy)
        self.canvas.draw_idle()

    def on_release(self, event):
        if event.button == 2: self.is_dragging = False
        self.press_x = self.press_y = None

    def align_angle(self, target_angle):
        max_ang = self.ang_speed_var.get()
        while self.is_running:
            diff_a = (target_angle - self.ra + math.pi) % (2 * math.pi) - math.pi
            if abs(diff_a) < 0.05: break
            ang_speed = np.clip(1.2 * diff_a, -max_ang, max_ang)
            if abs(ang_speed) < 0.15: ang_speed = 0.15 if ang_speed > 0 else -0.15
            self.send_command(0, ang_speed)
            time.sleep(0.05)
        self.send_command(0, 0)

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
        if self.current_telemetry:
            try:
                data = self.current_telemetry
                odom = data["p"]
                self.rx, self.ry, self.ra = odom['x'] + self.offset_x, odom['y'] + self.offset_y, odom['a']
                self.latest_lidar = np.array(data["s"], dtype=float) / 100.0

                self.pos_label.config(text=f"X: {self.rx:.2f} Y: {self.ry:.2f}")
                self.robot_dot.set_data([self.rx], [self.ry])
                self.robot_dir.set_data([self.rx, self.rx + 0.5 * math.cos(self.ra)],
                                        [self.ry, self.ry + 0.5 * math.sin(self.ra)])

                if not self.path_history_x or math.hypot(self.rx - self.path_history_x[-1],
                                                         self.ry - self.path_history_y[-1]) > 0.05:
                    self.path_history_x.append(self.rx)
                    self.path_history_y.append(self.ry)
                    self.path_plot.set_data(self.path_history_x, self.path_history_y)

                self.canvas.draw_idle()
            except:
                pass
        self.after(INTERVAL, self.update_status)

    def navigation_thread(self, target_list, mission_name="주행", is_reverse=False):
        self.log(f"▶ {mission_name} 시작")
        idx = 0
        while self.is_running and idx < len(target_list):
            tx, ty = target_list[idx]
            dist = math.hypot(tx - self.rx, ty - self.ry)

            if dist < WP_TOL:
                idx += 1;
                continue

            target_a = math.atan2(ty - self.ry, tx - self.rx)
            diff_a = (target_a - self.ra + math.pi) % (2 * math.pi) - math.pi

            lin = self.lin_speed_var.get() * (1.0 - abs(diff_a) / math.pi)
            ang = np.clip(1.5 * diff_a, -self.ang_speed_var.get(), self.ang_speed_var.get())
            self.send_command(lin, ang)
            time.sleep(0.05)

        self.send_command(0, 0)
        self.is_running = False
        self.log(f"🏁 {mission_name} 완료")

    def _create_menubar(self):
        menubar = tk.Menu(self)

        # 기존 주행제어 메뉴
        menu_nav = tk.Menu(menubar, tearoff=0)
        menu_nav.add_command(label="WP 주행 시작", command=self.start_navigation)
        menu_nav.add_separator()
        menu_nav.add_command(label="맵 리셋", command=self.reset_zoom)
        menubar.add_cascade(label="기본제어", menu=menu_nav)

        # [새로 추가] 청소 기능 메뉴
        menu_clean = tk.Menu(menubar, tearoff=0)
        menu_clean.add_command(label="청소 미션 시작(탐색+ㄹ자)", command=self.start_cleaning_mission)
        menu_clean.add_command(label="외곽 탐색만 수행", command=lambda: threading.Thread(target=self.follow_wall_and_mapping,
                                                                                   daemon=True).start())
        menubar.add_cascade(label="청소모드", menu=menu_clean)

        self.config(menu=menubar)

    def _create_layout(self):
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        self.main_container.rowconfigure(0, weight=6);
        self.main_container.columnconfigure(0, weight=1)

        self.center_frame = ttk.Frame(self.main_container)
        self.center_frame.grid(row=0, column=0, sticky="nsew")
        self.center_frame.columnconfigure(0, weight=5);
        self.center_frame.columnconfigure(1, weight=1)

        self.map_frame = ttk.Frame(self.center_frame)
        self.map_frame.grid(row=0, column=0, sticky="nsew")

        self.ctrl_panel = ttk.Frame(self.center_frame, padding=10)
        self.ctrl_panel.grid(row=0, column=1, sticky="nsew")

        self.pos_label = tk.Label(self.ctrl_panel, text="X: 0.00 Y: 0.00", font=('Courier', 11))
        self.pos_label.pack(pady=10)

        tk.Label(self.ctrl_panel, text="선속도").pack()
        self.lin_speed_var = tk.DoubleVar(value=DEFAULT_LIN)
        tk.Scale(self.ctrl_panel, from_=0.05, to=0.3, resolution=0.01, orient=tk.HORIZONTAL,
                 variable=self.lin_speed_var).pack(fill=tk.X)

        tk.Label(self.ctrl_panel, text="각속도").pack()
        self.ang_speed_var = tk.DoubleVar(value=DEFAULT_ANG)
        tk.Scale(self.ctrl_panel, from_=0.1, to=1.5, resolution=0.05, orient=tk.HORIZONTAL,
                 variable=self.ang_speed_var).pack(fill=tk.X)

        tk.Button(self.ctrl_panel, text="비상 정지", command=self.stop_mission, bg="red", fg="white").pack(fill=tk.X,
                                                                                                       pady=20)

        self.log_text = tk.Text(self.main_container, height=8, font=("Consolas", 9))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_aspect('equal');
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(-10, 10);
        self.ax.set_ylim(-10, 10)
        self.path_plot, = self.ax.plot([], [], 'g-', alpha=0.5)
        self.robot_dot, = self.ax.plot([], [], 'ro', markersize=8)
        self.robot_dir, = self.ax.plot([], [], 'r-')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def log(self, msg):
        ts = time.strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_queue.put((time.strftime('%Y-%m-%d %H:%M:%S'), "INFO", msg))

    def stop_mission(self):
        self.is_running = False
        self.send_command(0, 0)
        self.log("🛑 중지 명령")

    def on_map_click(self, event):
        if event.inaxes != self.ax or self.is_running: return
        if event.button == 1:  # WP 추가
            self.waypoints.append((event.xdata, event.ydata))
            self.ax.plot(event.xdata, event.ydata, 'bs', markersize=4)
            self.canvas.draw_idle()

    def on_scroll(self, event):
        if event.inaxes != self.ax: return
        scale = 0.9 if event.button == 'up' else 1.1
        cur_x, cur_y = self.ax.get_xlim(), self.ax.get_ylim()
        self.ax.set_xlim(event.xdata - (event.xdata - cur_x[0]) * scale, event.xdata + (cur_x[1] - event.xdata) * scale)
        self.ax.set_ylim(event.ydata - (event.ydata - cur_y[0]) * scale, event.ydata + (cur_y[1] - event.ydata) * scale)
        self.canvas.draw_idle()

    def reset_zoom(self):
        self.ax.set_xlim(-10, 10);
        self.ax.set_ylim(-10, 10)
        self.canvas.draw_idle()

    def start_navigation(self):
        if not self.waypoints: return
        self.is_running = True
        threading.Thread(target=self.navigation_thread, args=(self.waypoints, "WP 주행"), daemon=True).start()

    def on_close(self):
        self.db_worker_running = False
        if self.db_conn: self.db_conn.close()
        self.destroy()

    def _init_log_db_mysql(self):
        try:
            conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, autocommit=True)
            cur = conn.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
            conn.close()
            self.db_conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB,
                                           autocommit=True)
            self.db_cur = self.db_conn.cursor()
            self.db_cur.execute(
                f"CREATE TABLE IF NOT EXISTS {MYSQL_TABLE} (id BIGINT AUTO_INCREMENT PRIMARY KEY, ts DATETIME, level VARCHAR(10), msg TEXT)")
        except:
            print("DB 연결 실패")

    def _start_log_db_worker_mysql(self):
        self.db_worker_running = True

        def worker():
            while self.db_worker_running:
                try:
                    item = self.log_queue.get(timeout=0.5)
                except Empty:
                    continue
                if item is None: break
                try:
                    self.db_cur.execute(f"INSERT INTO {MYSQL_TABLE} (ts, level, msg) VALUES (%s, %s, %s)", item)
                except:
                    pass

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    AbsoluteMapZoomController().mainloop()