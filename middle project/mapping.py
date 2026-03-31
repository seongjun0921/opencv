import tkinter as tk
from tkinter import ttk
import math
import time
import requests
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

URL = "http://192.168.0.243:5000/control"
INTERVAL = 100  # ms

class RobotControlGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Global Robot Monitoring System (Zoomed Mode)")
        self.geometry("1200x800")

        self._create_menu()
        self._create_layout()

        self.after(INTERVAL, self.update_lidar)

    def _create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def _create_layout(self):
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.main_frame.rowconfigure(0, weight=2)
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.center_frame = ttk.Frame(self.main_frame)
        self.center_frame.grid(row=0, column=0, sticky="nsew")
        self.center_frame.columnconfigure(0, weight=5)
        self.center_frame.columnconfigure(1, weight=2)

        self.map_frame = ttk.Frame(self.center_frame)
        self.map_frame.grid(row=0, column=0, sticky="nsew")

        self.info_frame = ttk.Frame(self.center_frame)
        self.info_frame.grid(row=0, column=1, sticky="nsew")
        ttk.Label(self.info_frame, text="Robot Status", font=("Arial", 12, "bold")).pack(pady=10)

        self.status_label = ttk.Label(self.info_frame, text="X: 0.00\nY: 0.00\nA: 0.00°", font=("Courier", 10))
        self.status_label.pack(pady=5)

        self.fig = plt.Figure(figsize=(6, 6))
        self.ax = self.fig.add_subplot(111)

        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle='--', alpha=0.5)

        # 시각화 객체 설정 (점이 너무 작게 보이지 않도록 s=10으로 상향)
        self.scat = self.ax.scatter([], [], s=10, c="blue", label="Obstacles")
        self.robot_dot, = self.ax.plot([], [], 'ro', markersize=12, label="Robot", zorder=5)
        self.robot_dir, = self.ax.plot([], [], 'r-', linewidth=3, zorder=6)

        self.ax.legend(loc='upper right')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.log_frame = ttk.Frame(self.main_frame)
        self.log_frame.grid(row=1, column=0, sticky="nsew")
        self.log_text = tk.Text(self.log_frame, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log("System Initialized - Zoomed View (10x)")

    def update_lidar(self):
        try:
            res = requests.get(URL, timeout=0.2)
            data = res.json()

            rx = data["p"]["x"]
            ry = data["p"]["y"]
            ra = data["p"]["a"] + math.pi

            distances = np.array(data["s"], dtype=float) / 100.0
            valid_mask = (distances > 0.05) & (distances < 30.0)
            valid_dist = distances[valid_mask]

            rel_angles = np.linspace(0, 2 * np.pi, len(distances), endpoint=False)
            valid_angles = rel_angles[valid_mask]

            world_x = rx + valid_dist * np.cos(valid_angles + ra)
            world_y = ry + valid_dist * np.sin(valid_angles + ra)

            self.scat.set_offsets(np.c_[world_x, world_y])
            self.robot_dot.set_data([rx], [ry])

            line_len = 0.3 # 줌인 상태이므로 헤딩선 길이도 적절히 조절
            self.robot_dir.set_data(
                [rx, rx + line_len * math.cos(ra)],
                [ry, ry + line_len * math.sin(ra)]
            )

            # [핵심 변경: 줌인 설정]
            # view_dist가 작을수록 화면 내의 데이터는 상대적으로 크게 보입니다.
            # 기존 15m에서 2m~3m 정도로 줄이면 약 5~7배 크게 보입니다.
            # 10배 정도의 느낌을 원하시면 1.5 ~ 2.0을 추천합니다.
            view_dist = 1.7
            self.ax.set_xlim(rx - view_dist, rx + view_dist)
            self.ax.set_ylim(ry - view_dist, ry + view_dist)

            self.status_label.config(text=f"X: {rx:.3f}\nY: {ry:.3f}\nA: {math.degrees(ra):.1f}°")
            self.canvas.draw_idle()

        except Exception as e:
            pass

        self.after(INTERVAL, self.update_lidar)

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    app = RobotControlGUI()
    app.mainloop()